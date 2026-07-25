import heapq
import tracemalloc


class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = {i: [] for i in range(vertices)}

    def add_edge(self, u, v, w):
        self.graph[u].append((v, w))

    def dijkstra(self, src):
        """Requires non-negative edge weights. A negative-weight cycle lets
        relaxation improve a distance indefinitely, so `pq` never drains and this
        loops forever -- Dijkstra doesn't detect that case itself; use
        bellman_ford (which does) to check first if weights might be negative."""
        distances = {i: float('inf') for i in range(self.V)}
        distances[src] = 0
        pq = [(0, src)]
        while pq:
            current_dist, u = heapq.heappop(pq)
            if current_dist > distances[u]:
                continue
            for v, weight in self.graph[u]:
                distance = current_dist + weight
                if distance < distances[v]:
                    distances[v] = distance
                    heapq.heappush(pq, (distance, v))
        return distances

    def bellman_ford(self, src):
        """Early-exits as soon as a full pass makes no update -- correct because once
        a pass is a no-op, every further pass would be too (no distance changed for
        the relaxation to build on). `last_bf_passes` records how many passes actually
        ran, for the measurement-trap experiment below."""
        distances = {i: float('inf') for i in range(self.V)}
        distances[src] = 0
        passes_run = 0
        for _ in range(self.V - 1):
            passes_run += 1
            updated = False
            for u in range(self.V):
                for v, w in self.graph[u]:
                    if distances[u] != float('inf') and distances[u] + w < distances[v]:
                        distances[v] = distances[u] + w
                        updated = True
            if not updated:
                break
        self.last_bf_passes = passes_run
        for u in range(self.V):
            for v, w in self.graph[u]:
                if distances[u] != float('inf') and distances[u] + w < distances[v]:
                    return "Graph contains negative weight cycle"
        return distances

    def prim(self, src=0):
        visited = [False] * self.V
        min_heap = [(0, src, -1)]
        mst_edges = []
        total_cost = 0
        while min_heap:
            weight, u, parent = heapq.heappop(min_heap)
            if visited[u]:
                continue
            visited[u] = True
            total_cost += weight
            if parent != -1:
                mst_edges.append((parent, u, weight))
            for v, w in self.graph[u]:
                if not visited[v]:
                    heapq.heappush(min_heap, (w, v, u))
        return mst_edges, total_cost

    def to_adjacency_matrix(self):
        """Dense V x V representation: matrix[u][v] is the edge weight, or inf if
        no edge; 0 on the diagonal. Costs O(V^2) space regardless of edge count --
        that's what `memory_comparison` measures against the adjacency list's
        O(V + E)."""
        matrix = [[float('inf')] * self.V for _ in range(self.V)]
        for i in range(self.V):
            matrix[i][i] = 0
        for u, edges in self.graph.items():
            for v, w in edges:
                matrix[u][v] = w
        return matrix

    def memory_comparison(self):
        """tracemalloc-measured bytes for this graph's adjacency-list storage vs
        an equivalent adjacency matrix. Returns {'adjacency_list_bytes': ...,
        'adjacency_matrix_bytes': ...}; on a sparse graph the list wins, and the
        gap grows with V since the matrix is O(V^2) regardless of edge count."""
        tracemalloc.start()
        try:
            before = tracemalloc.get_traced_memory()[0]
            adjacency_copy = {u: list(edges) for u, edges in self.graph.items()}
            list_bytes = tracemalloc.get_traced_memory()[0] - before
            del adjacency_copy

            before = tracemalloc.get_traced_memory()[0]
            matrix = self.to_adjacency_matrix()
            matrix_bytes = tracemalloc.get_traced_memory()[0] - before
            del matrix
        finally:
            tracemalloc.stop()
        return {'adjacency_list_bytes': list_bytes, 'adjacency_matrix_bytes': matrix_bytes}

    def verify_with_networkx(self, src=0):
        """Cross-checks dijkstra/bellman_ford/prim against NetworkX, if it's
        installed. NetworkX is optional (this repo is otherwise stdlib-only), so
        this returns {'available': False, ...} instead of raising when it isn't.

        Runs bellman_ford before dijkstra specifically to detect negative weights
        first: dijkstra is undefined for those and infinite-loops on a negative
        cycle (see its docstring), so this skips that comparison entirely rather
        than calling it and hanging."""
        try:
            import networkx as nx
        except ImportError:
            return {'available': False, 'message': "networkx is not installed; skipping verification"}

        directed = nx.DiGraph()
        directed.add_nodes_from(range(self.V))
        for u, edges in self.graph.items():
            for v, w in edges:
                directed.add_edge(u, v, weight=w)

        mine_bf = self.bellman_ford(src)
        has_negative_weight = any(w < 0 for edges in self.graph.values() for _, w in edges)

        if has_negative_weight:
            dijkstra_match = None  # not applicable: dijkstra requires non-negative weights
        else:
            mine_dijkstra = self.dijkstra(src)
            nx_dijkstra = nx.single_source_dijkstra_path_length(directed, src, weight='weight')
            dijkstra_match = all(
                nx_dijkstra.get(v, float('inf')) == mine_dijkstra[v] for v in range(self.V)
            )
        if isinstance(mine_bf, str):
            try:
                nx.single_source_bellman_ford_path_length(directed, src, weight='weight')
                bf_match = False  # we found a negative cycle, networkx didn't
            except nx.NetworkXUnbounded:
                bf_match = True
        else:
            try:
                nx_bf = nx.single_source_bellman_ford_path_length(directed, src, weight='weight')
                bf_match = all(nx_bf.get(v, float('inf')) == mine_bf[v] for v in range(self.V))
            except nx.NetworkXUnbounded:
                bf_match = False

        undirected = nx.Graph()
        undirected.add_nodes_from(range(self.V))
        for u, edges in self.graph.items():
            for v, w in edges:
                undirected.add_edge(u, v, weight=w)
        _, mine_mst_weight = self.prim(src)
        nx_mst_weight = sum(
            d['weight'] for _, _, d in nx.minimum_spanning_tree(undirected, algorithm='prim').edges(data=True)
        )
        mst_match = abs(nx_mst_weight - mine_mst_weight) < 1e-9

        return {
            'available': True,
            'dijkstra_match': dijkstra_match,
            'bellman_ford_match': bf_match,
            'mst_weight_match': mst_match,
        }


def chain_graph(n, weight=1):
    """Directed chain n-1 -> n-2 -> ... -> 0: the actual Bellman-Ford worst case
    for this implementation. bellman_ford relaxes u in ascending order (0..V-1)
    every pass; walking the chain in descending order means each pass can only
    push the shortest-path frontier forward by one hop, so it takes exactly V-1
    passes to reach vertex 0 -- early exit triggers on the last possible pass and
    saves nothing. (A chain built 0->1->...->n-1 would relax in the *same* order
    bellman_ford iterates, collapsing the whole path in one pass -- the opposite
    of worst case.) Call bellman_ford(n - 1) with the source at the high end."""
    g = Graph(n)
    for i in range(n - 1, 0, -1):
        g.add_edge(i, i - 1, weight)
    return g


def star_graph(n, weight=1):
    """Undirected-in-effect star: source 0 directly reaches every other vertex.
    One pass relaxes every edge, so early exit stops after pass 1 -- the opposite
    extreme from the chain."""
    g = Graph(n)
    for i in range(1, n):
        g.add_edge(0, i, weight)
    return g


def measurement_trap_experiment(n=50):
    """Demonstrates that early exit's payoff depends on graph shape, not just
    size: on a chain it runs the full n-1 passes (no savings), on a star it stops
    after 1 pass. A wall-clock comparison alone would miss this -- pass count is
    the metric that isolates the effect from timing noise."""
    chain = chain_graph(n)
    chain.bellman_ford(n - 1)
    star = star_graph(n)
    star.bellman_ford(0)
    return {
        'naive_passes': n - 1,
        'chain_passes_run': chain.last_bf_passes,
        'star_passes_run': star.last_bf_passes,
    }
