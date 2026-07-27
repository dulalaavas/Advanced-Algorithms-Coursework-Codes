"""Task 4 - NP-Hard Problem: VRPTW with four heuristics plus an independent feasibility verifier."""
import math
import random
from dataclasses import dataclass

@dataclass(frozen=True)
class Customer:
    cid: int
    x: float
    y: float
    demand: int
    ready: float      # earliest service start
    due: float        # latest service start
    service: float    # service duration

class VRPTW:
    """Customer 0 is the depot; minimise total travel distance under capacity and time windows."""
    def __init__(self, customers, capacity):
        self.customers = customers
        self.capacity = capacity
        self.n = len(customers)
        self.depot = customers[0]
        # Distance matrix precomputed once; every heuristic queries it inline.
        self.d = [[0.0] * self.n for _ in range(self.n)]
        for i in range(self.n):
            for j in range(self.n):
                self.d[i][j] = math.dist((customers[i].x, customers[i].y),
                                         (customers[j].x, customers[j].y))

    def route_feasible(self, route):
        """route: list of customer ids, without the depot at either end."""
        if sum(self.customers[c].demand for c in route) > self.capacity:
            return False
        t = 0.0
        prev = 0
        for c in route:
            t += self.d[prev][c]
            cust = self.customers[c]
            if t > cust.due:
                return False
            t = max(t, cust.ready) + cust.service
            prev = c
        t += self.d[prev][0]
        return t <= self.depot.due

    def route_cost(self, route):
        if not route:
            return 0.0
        c = self.d[0][route[0]]
        for a, b in zip(route, route[1:]):
            c += self.d[a][b]
        c += self.d[route[-1]][0]
        return c

    def solution_cost(self, routes):
        return sum(self.route_cost(r) for r in routes)

    def verify(self, routes):
        """Independent check: each customer served once, all routes feasible. Returns (ok, reason)."""
        served = [c for r in routes for c in r]
        if sorted(served) != list(range(1, self.n)):
            return False, f"customers served {len(served)}, expected {self.n - 1}, or duplicates"
        for i, r in enumerate(routes):
            if not self.route_feasible(r):
                return False, f"route {i} infeasible"
        return True, "ok"

# --- Heuristic 1: Greedy construction (nearest feasible neighbour) ---
def greedy_construct(inst, rng=None, rcl_size=1):
    """Append the nearest feasible customer, one vehicle at a time; rcl_size > 1 is the GRASP variant."""
    unvisited = set(range(1, inst.n))
    routes = []
    while unvisited:
        route = []
        while True:
            last = route[-1] if route else 0
            candidates = []
            for c in unvisited:
                if inst.route_feasible(route + [c]):
                    candidates.append((inst.d[last][c], c))
            if not candidates:
                break
            candidates.sort()
            k = min(rcl_size, len(candidates))
            _, chosen = candidates[rng.randrange(k)] if (rng and k > 1) else candidates[0]
            route.append(chosen)
            unvisited.remove(chosen)
        if not route:
            raise RuntimeError("infeasible instance: a customer cannot be served at all")
        routes.append(route)
    return routes

# --- Heuristic 2: Local search (2-opt intra-route + relocate inter-route) ---
def local_search(inst, routes, max_passes=50):
    """First-improvement over two neighbourhoods: 2-opt (segment reversal) and relocate; every move is feasibility-checked."""
    routes = [list(r) for r in routes]
    for _ in range(max_passes):
        improved = False
        # 2-opt within each route
        for r in routes:
            n = len(r)
            for i in range(n - 1):
                for j in range(i + 2, n):
                    new = r[:i + 1] + r[i + 1:j + 1][::-1] + r[j + 1:]
                    if inst.route_cost(new) < inst.route_cost(r) - 1e-9 and inst.route_feasible(new):
                        r[:] = new
                        improved = True
        # relocate between routes
        for a in range(len(routes)):
            for pos_a in range(len(routes[a])):
                cust = routes[a][pos_a]
                base = inst.route_cost(routes[a])
                without = routes[a][:pos_a] + routes[a][pos_a + 1:]
                gain_remove = base - inst.route_cost(without)
                for b in range(len(routes)):
                    if a == b:
                        continue
                    for pos_b in range(len(routes[b]) + 1):
                        trial = routes[b][:pos_b] + [cust] + routes[b][pos_b:]
                        delta_add = inst.route_cost(trial) - inst.route_cost(routes[b])
                        if delta_add < gain_remove - 1e-9 and inst.route_feasible(trial):
                            routes[a] = without
                            routes[b] = trial
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
        routes = [r for r in routes if r]
        if not improved:
            break
    return routes

# --- Heuristic 3: GRASP (Greedy Randomised Adaptive Search Procedure) ---
def grasp(inst, iterations=20, rcl_size=3, seed=0, ls_passes=50):
    """Randomised construction + local search, keeping the best over iterations."""
    rng = random.Random(seed)
    best, best_cost = None, float('inf')
    for _ in range(iterations):
        sol = greedy_construct(inst, rng=rng, rcl_size=rcl_size)
        sol = local_search(inst, sol, max_passes=ls_passes)
        c = inst.solution_cost(sol)
        if c < best_cost:
            best, best_cost = sol, c
    return best

# --- Heuristic 4: Simulated Annealing ---
def simulated_annealing(inst, routes, seed=0, iterations=8000,
                        t0=50.0, t_final=0.01, polish=True):
    """Metropolis acceptance over relocate/swap moves; infeasible neighbours are rejected, not penalised."""
    rng = random.Random(seed)
    cur = [list(r) for r in routes]
    cur_cost = inst.solution_cost(cur)
    best, best_cost = [list(r) for r in cur], cur_cost
    T = t0
    cooling = (t_final / t0) ** (1.0 / max(iterations, 1))
    accepted = rejected_infeasible = 0
    for _ in range(iterations):
        if len(cur) == 0:
            break
        cand = [list(r) for r in cur]
        if rng.random() < 0.5:
            a = rng.randrange(len(cand))
            if not cand[a]:
                T *= cooling
                continue
            pos_a = rng.randrange(len(cand[a]))
            cust = cand[a].pop(pos_a)
            b = rng.randrange(len(cand))
            pos_b = rng.randrange(len(cand[b]) + 1)
            cand[b].insert(pos_b, cust)
        else:
            a = rng.randrange(len(cand))
            b = rng.randrange(len(cand))
            if not cand[a] or not cand[b]:
                T *= cooling
                continue
            i = rng.randrange(len(cand[a]))
            j = rng.randrange(len(cand[b]))
            cand[a][i], cand[b][j] = cand[b][j], cand[a][i]
        cand = [r for r in cand if r]
        if not all(inst.route_feasible(r) for r in cand):
            rejected_infeasible += 1
            T *= cooling
            continue
        c = inst.solution_cost(cand)
        delta = c - cur_cost
        if delta < 0 or rng.random() < math.exp(-delta / max(T, 1e-12)):
            cur, cur_cost = cand, c
            accepted += 1
            if c < best_cost:
                best, best_cost = [list(r) for r in cand], c
        T *= cooling
    simulated_annealing.last_stats = {  # type: ignore[attr-defined]
        'accepted': accepted,
        'rejected_infeasible': rejected_infeasible,
        'final_T': T,
    }
    if polish:
        best = local_search(inst, best, max_passes=10)
    return best

# --- Synthetic (Solomon-like) instance generator ---
def make_instance(n_customers, seed=1, capacity=200, horizon=1000.0):
    rng = random.Random(seed)
    depot = Customer(0, 50.0, 50.0, 0, 0.0, horizon, 0.0)
    customers = [depot]
    for i in range(1, n_customers + 1):
        x, y = rng.uniform(0, 100), rng.uniform(0, 100)
        travel = math.dist((x, y), (50.0, 50.0))
        width = rng.uniform(150, 350)
        earliest = rng.uniform(travel, max(travel, horizon * 0.55))
        ready = max(0.0, earliest)
        due = min(horizon - travel - 10, ready + width)
        if due < ready:
            ready, due = travel, travel + width
        customers.append(Customer(i, x, y, rng.randint(5, 30), ready, due, 10.0))
    return VRPTW(customers, capacity)
