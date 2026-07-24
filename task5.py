"""
Task 5 - Concurrent Programming: parallel merge sort of the Task 1 city dataset.

Sequential baseline, a threaded version (mutex-guarded shared state) and a
process-based version (multiprocessing), measuring speedup at 1/2/4/8 workers.

Caveat: the machine this was run on reports os.cpu_count() == 1, so the speedup
curve measures overhead, not scaling. The harness is written to be re-run on
multi-core hardware.
"""
import random
import threading
import multiprocessing
import time


# --- core algorithm ---
def merge(left, right):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def merge_sort(a):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    return merge(merge_sort(a[:mid]), merge_sort(a[mid:]))


def merge_all(chunks):
    """Pairwise-merge sorted chunks into one sorted list."""
    while len(chunks) > 1:
        nxt = []
        for i in range(0, len(chunks), 2):
            if i + 1 < len(chunks):
                nxt.append(merge(chunks[i], chunks[i + 1]))
            else:
                nxt.append(chunks[i])
        chunks = nxt
    return chunks[0] if chunks else []


def split(data, k):
    n = len(data)
    size = (n + k - 1) // k
    return [data[i:i + size] for i in range(0, n, size)] or [[]]


# --- sequential baseline ---
def sequential_sort(data):
    return merge_sort(list(data))


# --- threaded ---
# Shared state guarded by a mutex: `value += n` is a non-atomic read-modify-write
# (LOAD_FAST / ADD / STORE_FAST), so a thread switch between those bytecodes can
# lose an update.
class Counter:
    def __init__(self, use_lock=True):
        self.value = 0
        self.use_lock = use_lock
        self.lock = threading.Lock()

    def add(self, n):
        if self.use_lock:
            with self.lock:
                self.value += n
        else:
            self.value += n


def threaded_sort(data, num_threads, counter=None):
    chunks = split(list(data), num_threads)
    results = [None] * len(chunks)

    def worker(idx, chunk):
        r = merge_sort(chunk)
        results[idx] = r                    # distinct index per thread: no race
        if counter is not None:
            counter.add(len(r))             # shared: needs the mutex

    threads = [threading.Thread(target=worker, args=(i, c))
               for i, c in enumerate(chunks)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return merge_all(results)


# --- process-based ---
def _proc_worker(chunk):
    return merge_sort(chunk)


def process_sort(data, num_procs):
    chunks = split(list(data), num_procs)
    with multiprocessing.Pool(num_procs) as pool:
        results = pool.map(_proc_worker, chunks)
    return merge_all(results)


# --- race condition demonstration ---
def demonstrate_race(num_threads=8, increments=50_000, use_lock=False):
    """Each thread does `increments` unguarded +1 operations. Any shortfall from
    num_threads * increments is a lost update from a thread switch between the
    LOAD and the STORE."""
    counter = Counter(use_lock=use_lock)

    def worker():
        for _ in range(increments):
            counter.add(1)

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0
    expected = num_threads * increments
    return counter.value, expected, elapsed


def make_data(n, seed=0):
    rng = random.Random(seed)
    return [rng.random() for _ in range(n)]
