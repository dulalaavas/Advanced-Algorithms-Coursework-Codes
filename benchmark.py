import time
import random
import statistics
import csv
import sys

from bst import BST
from avl import AVLTree
from hashtable import HashTable
from minheap import MinHeap
from city import City


def make_cities(n, seed):
    rng = random.Random(seed)
    return [City(i, f"City_{i}", rng.uniform(-90, 90), rng.uniform(-180, 180),
                 rng.randint(1000, 5_000_000)) for i in range(n)]


def time_keyed_structure(factory, cities, insert_order, search_keys, delete_order):
    struct = factory()
    t0 = time.perf_counter()
    for cid in insert_order:
        struct.insert(cid, cities[cid])
    t_insert = time.perf_counter() - t0

    t0 = time.perf_counter()
    for cid in search_keys:
        struct.search(cid)
    t_search = time.perf_counter() - t0

    t0 = time.perf_counter()
    for cid in delete_order:
        struct.delete(cid)
    t_delete = time.perf_counter() - t0
    return t_insert, t_search, t_delete


def time_heap(cities, insert_order):
    heap = MinHeap()
    t0 = time.perf_counter()
    for cid in insert_order:
        c = cities[cid]
        heap.push(c.distance, c)
    t_push = time.perf_counter() - t0

    t0 = time.perf_counter()
    while len(heap) > 0:
        heap.pop()
    t_pop = time.perf_counter() - t0
    return t_push, t_pop


def run_trials(n, trials, seed_base):
    results = {
        'BST': {'insert': [], 'search': [], 'delete': []},
        'AVL': {'insert': [], 'search': [], 'delete': []},
        'Hash': {'insert': [], 'search': [], 'delete': []},
        'Heap': {'push': [], 'pop': []},
    }
    for trial in range(trials):
        seed = seed_base + trial
        rng = random.Random(seed)
        cities = make_cities(n, seed)
        insert_order = list(range(n))
        rng.shuffle(insert_order)
        search_keys = list(range(n))
        rng.shuffle(search_keys)
        delete_order = list(range(n))
        rng.shuffle(delete_order)

        for name, factory in [('BST', BST), ('AVL', AVLTree), ('Hash', HashTable)]:
            ti, ts, td = time_keyed_structure(factory, cities, insert_order, search_keys, delete_order)
            results[name]['insert'].append(ti)
            results[name]['search'].append(ts)
            results[name]['delete'].append(td)

        tp, tpop = time_heap(cities, insert_order)
        results['Heap']['push'].append(tp)
        results['Heap']['pop'].append(tpop)
    return results


def summarize(results):
    summary = {}
    for struct_name, ops in results.items():
        summary[struct_name] = {}
        for op_name, times in ops.items():
            summary[struct_name][op_name] = {
                'mean': statistics.mean(times),
                'stdev': statistics.stdev(times) if len(times) > 1 else 0.0,
                'min': min(times),
                'max': max(times),
            }
    return summary


def main():
    ns = [100, 1000, 10000]
    trials = 5
    all_summaries = {}
    for n in ns:
        print(f"Running N={n} ({trials} trials)...", file=sys.stderr)
        all_summaries[n] = summarize(run_trials(n, trials, seed_base=1000 * n))

    with open('benchmark_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['N', 'structure', 'operation', 'mean_seconds',
                         'stdev_seconds', 'min_seconds', 'max_seconds'])
        for n in ns:
            for struct_name, ops in all_summaries[n].items():
                for op_name, stats in ops.items():
                    writer.writerow([n, struct_name, op_name,
                                     f"{stats['mean']:.6f}", f"{stats['stdev']:.6f}",
                                     f"{stats['min']:.6f}", f"{stats['max']:.6f}"])

    for n in ns:
        print(f"\n=== N = {n} (mean of {trials} trials, seconds) ===")
        for struct_name, ops in all_summaries[n].items():
            for op_name, stats in ops.items():
                print(f"  {struct_name:6s} {op_name:8s} "
                      f"mean={stats['mean']:.6f}s stdev={stats['stdev']:.6f}s")
    return all_summaries


if __name__ == '__main__':
    main()
