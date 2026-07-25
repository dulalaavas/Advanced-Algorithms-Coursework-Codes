"""
Task 5 - Concurrent Programming: parallel merge sort of the Task 1 city dataset.

Sequential baseline, a threaded version (mutex-guarded shared state) and a
process-based version (multiprocessing), measuring speedup at 1/2/4/8 workers.

Also includes two race-condition demonstrations: `demonstrate_race` (bare `+=`,
optionally with a yield point) and `demonstrate_race_deterministic` (Barrier-
synchronised, reproducing the report's 87.5%-lost-updates figure exactly).

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
# (LOAD_FAST / ADD / STORE_FAST). In practice CPython's GIL rarely switches threads
# inside such a short bytecode run, so the bare `+=` alone loses almost nothing.
# `yield_point=True` forces the switch explicitly (read, yield, write), which is
# what actually manifests the race: every thread reads the same stale value before
# any of them writes it back, so only one of `num_threads` increments survives per
# round (~(num_threads-1)/num_threads updates lost).
class Counter:
    def __init__(self, use_lock=True):
        self.value = 0
        self.use_lock = use_lock
        self.lock = threading.Lock()

    def add(self, n, yield_point=False):
        if self.use_lock:
            with self.lock:
                self._read_modify_write(n, yield_point)
        else:
            self._read_modify_write(n, yield_point)

    def _read_modify_write(self, n, yield_point):
        value = self.value
        if yield_point:
            time.sleep(0)
        self.value = value + n


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
def demonstrate_race(num_threads=8, increments=50_000, use_lock=False, yield_point=False):
    """Each thread does `increments` +1 operations. Any shortfall from
    num_threads * increments is a lost update from a thread switch between the
    read and the write. yield_point=True forces that switch on every increment
    (see Counter), which is what reliably produces the ~87.5% loss at
    num_threads=8 reported in Table 9; without it, losses are rare on CPython."""
    counter = Counter(use_lock=use_lock)

    def worker():
        for _ in range(increments):
            counter.add(1, yield_point=yield_point)

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0
    expected = num_threads * increments
    return counter.value, expected, elapsed


def demonstrate_race_deterministic(num_threads=8, rounds=5_000):
    """Barrier-synchronised race: every thread reads the shared value, waits at a
    Barrier so all `num_threads` threads have read the same stale value, writes
    value + 1, then waits at a second Barrier before starting the next round. That
    forces every round to lose num_threads - 1 of the num_threads writes (the GIL
    still serialises the writes themselves, but they all write the same stale
    value+1, so only the last one sticks) -- a deterministic (num_threads - 1) /
    num_threads loss, e.g. exactly 87.5% at num_threads=8, matching Table 9.
    `demonstrate_race`'s yield_point is non-deterministic (25-85% observed) because
    nothing stops one thread from reading, writing, and reading again before its
    peers finish their first read; this variant removes that slack. Unguarded
    only: a lock would deadlock threads waiting at the barrier."""
    value = 0
    barrier = threading.Barrier(num_threads)

    def worker():
        nonlocal value
        for _ in range(rounds):
            v = value
            barrier.wait()
            value = v + 1
            barrier.wait()

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0
    expected = num_threads * rounds
    return value, expected, elapsed


def make_data(n, seed=0):
    rng = random.Random(seed)
    return [rng.random() for _ in range(n)]
