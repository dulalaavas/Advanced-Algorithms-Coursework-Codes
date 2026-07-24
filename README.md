# Advanced Algorithms Coursework Codes

Python implementations for an advanced data-structures and algorithms coursework.
Each file is self-contained and runnable with Python 3 (standard library only).

## Contents

| File | Topic |
|---|---|
| `city.py` | City record with Euclidean distance from a fixed origin |
| `bst.py` | Unbalanced Binary Search Tree (iterative insert/search/delete/height) |
| `avl.py` | Self-balancing AVL tree (balance-factor rotations) |
| `hashtable.py` | Hash table with separate chaining, prime capacity, resize at load factor 0.7 |
| `minheap.py` | Array-backed binary min-heap priority queue with tie-breaking |
| `benchmark.py` | Timing harness comparing BST / AVL / Hash / Heap at N = 100 / 1,000 / 10,000 |
| `task2_graphs.py` | Graph shortest paths: Dijkstra and Bellman-Ford |
| `task3.py` | Algorithmic strategies: DP (weighted job scheduling), greedy (min platforms), backtracking (Knight's Tour with Warnsdorff) |
| `task4.py` | NP-hard VRPTW: greedy, local search, GRASP, and simulated annealing heuristics |
| `task5.py` | Concurrent programming: sequential / threaded / multiprocessing merge sort |

## Running

```bash
python3 benchmark.py        # runs the Task 1 timing comparison, writes benchmark_results.csv
```

Modules in `task3.py`, `task4.py`, and `task5.py` expose functions intended to be
imported and called (they include exact/reference implementations for verification).

## Requirements

Python 3.8+ — no third-party dependencies.
