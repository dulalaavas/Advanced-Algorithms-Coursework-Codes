"""
Task 3 - Algorithmic Strategies
DP:           Weighted Job Scheduling with time windows
Greedy:       Minimum Number of Platforms
Backtracking: Knight's Tour with Warnsdorff pruning

Each paradigm is paired with an exact/unpruned reference so the report's claims
are measured rather than asserted.
"""
from bisect import bisect_right
from itertools import combinations
import sys


# --- 1. Dynamic Programming: Weighted Job Scheduling ---
# Job = (start, end, profit); choose a non-overlapping subset maximising profit.
# OPT(i) = max(OPT(i-1), profit_i + OPT(p(i))) over jobs sorted by end time,
# where p(i) is the rightmost job j < i with end_j <= start_i.

def weighted_job_scheduling(jobs):
    """Bottom-up DP. O(N log N) time, O(N) space. Returns (max_profit, chosen)."""
    if not jobs:
        return 0, []
    jobs = sorted(jobs, key=lambda j: j[1])
    ends = [j[1] for j in jobs]
    n = len(jobs)
    dp = [0] * (n + 1)
    take = [False] * (n + 1)
    for i in range(1, n + 1):
        start_i, end_i, profit_i = jobs[i - 1]
        p = bisect_right(ends, start_i, 0, i - 1)
        include = profit_i + dp[p]
        if include > dp[i - 1]:
            dp[i] = include
            take[i] = True
        else:
            dp[i] = dp[i - 1]
    chosen = []
    i = n
    while i > 0:
        if take[i]:
            chosen.append(jobs[i - 1])
            i = bisect_right(ends, jobs[i - 1][0], 0, i - 1)
        else:
            i -= 1
    return dp[n], list(reversed(chosen))


def weighted_job_scheduling_memo(jobs):
    """Top-down memoised variant. Same recurrence; the O(N) recursion stack is
    the practical difference from the bottom-up version."""
    if not jobs:
        return 0
    jobs = sorted(jobs, key=lambda j: j[1])
    ends = [j[1] for j in jobs]
    memo = {}

    def opt(i):
        if i == 0:
            return 0
        if i in memo:
            return memo[i]
        start_i, _, profit_i = jobs[i - 1]
        p = bisect_right(ends, start_i, 0, i - 1)
        memo[i] = max(opt(i - 1), profit_i + opt(p))
        return memo[i]

    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, len(jobs) + 100))
    try:
        return opt(len(jobs))
    finally:
        sys.setrecursionlimit(old)


def weighted_job_scheduling_bruteforce(jobs):
    """Exact reference: try every subset. O(2^N * N). Small N only."""
    best = 0
    for r in range(len(jobs) + 1):
        for combo in combinations(jobs, r):
            ordered = sorted(combo, key=lambda j: j[0])
            if all(ordered[k][1] <= ordered[k + 1][0] for k in range(len(ordered) - 1)):
                best = max(best, sum(j[2] for j in combo))
    return best


# --- 2. Greedy: Minimum Number of Platforms ---
# Sweep sorted arrivals/departures: +1 platform per arrival, -1 per departure,
# track the running max. Convention: arr <= dep counts as overlap.

def min_platforms_greedy(arrivals, departures):
    """O(N log N) time, O(N) space. Does not mutate inputs."""
    if not arrivals:
        return 0
    arr = sorted(arrivals)
    dep = sorted(departures)
    n = len(arr)
    i = j = 0
    current = best = 0
    while i < n:
        if arr[i] <= dep[j]:
            current += 1
            best = max(best, current)
            i += 1
        else:
            current -= 1
            j += 1
    return best


def min_platforms_exact(arrivals, departures):
    """Exact reference: max trains simultaneously present, checked at every
    arrival instant (where the max must occur). O(N^2)."""
    if not arrivals:
        return 0
    best = 0
    for t in arrivals:
        count = sum(1 for a, d in zip(arrivals, departures) if a <= t <= d)
        best = max(best, count)
    return best


# --- 3. Backtracking: Knight's Tour ---
MOVES = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]


def _valid(x, y, n, board):
    return 0 <= x < n and 0 <= y < n and board[x][y] == -1


def knights_tour(n, start=(0, 0), warnsdorff=False, node_cap=5_000_000):
    """Backtracking Knight's Tour. warnsdorff=True orders candidate moves by
    fewest onward moves first. Returns (board_or_None, nodes_explored, hit_cap),
    where nodes_explored is the number of square placements attempted."""
    board = [[-1] * n for _ in range(n)]
    sx, sy = start
    board[sx][sy] = 0
    stats = {'nodes': 0, 'cap': False}

    def onward_count(x, y):
        return sum(1 for dx, dy in MOVES if _valid(x + dx, y + dy, n, board))

    def solve(x, y, step):
        if step == n * n:
            return True
        candidates = [(x + dx, y + dy) for dx, dy in MOVES
                      if _valid(x + dx, y + dy, n, board)]
        if warnsdorff:
            candidates.sort(key=lambda c: onward_count(c[0], c[1]))
        for nx, ny in candidates:
            stats['nodes'] += 1
            if stats['nodes'] > node_cap:
                stats['cap'] = True
                return False
            board[nx][ny] = step
            if solve(nx, ny, step + 1):
                return True
            board[nx][ny] = -1
        return False

    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, n * n + 100))
    try:
        found = solve(sx, sy, 1)
    finally:
        sys.setrecursionlimit(old)
    return (board if found else None), stats['nodes'], stats['cap']


def verify_tour(board, n):
    """Independent check: every square visited once, consecutive steps a legal
    knight move."""
    if sorted(v for row in board for v in row) != list(range(n * n)):
        return False
    pos = {}
    for x in range(n):
        for y in range(n):
            pos[board[x][y]] = (x, y)
    for s in range(n * n - 1):
        (x1, y1), (x2, y2) = pos[s], pos[s + 1]
        if (abs(x1 - x2), abs(y1 - y2)) not in [(1, 2), (2, 1)]:
            return False
    return True
