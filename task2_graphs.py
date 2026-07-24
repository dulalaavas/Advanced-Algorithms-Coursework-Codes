import heapq


class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = {i: [] for i in range(vertices)}

    def add_edge(self, u, v, w):
        self.graph[u].append((v, w))

    def dijkstra(self, src):
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
        distances = {i: float('inf') for i in range(self.V)}
        distances[src] = 0
        for _ in range(self.V - 1):
            for u in range(self.V):
                for v, w in self.graph[u]:
                    if distances[u] != float('inf') and distances[u] + w < distances[v]:
                        distances[v] = distances[u] + w
        for u in range(self.V):
            for v, w in self.graph[u]:
                if distances[u] != float('inf') and distances[u] + w < distances[v]:
                    return "Graph contains negative weight cycle"
        return distances

# --- TODO: Prim's Algorithm not yet implemented ---
