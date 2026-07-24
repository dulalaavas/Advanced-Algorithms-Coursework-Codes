class MinHeap:
    """Array-backed binary min-heap priority queue. Entries are stored as
    (priority, counter, item); the counter is a tie-breaker so equal-priority
    items never fall through to comparing `item` directly. Arbitrary-key delete
    is O(N) (linear scan); only pop (extract-min) is O(log N)."""
    def __init__(self):
        self.heap = []
        self._counter = 0

    def push(self, priority, item):
        self.heap.append((priority, self._counter, item))
        self._counter += 1
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        """Extract and return (priority, item) with the smallest priority."""
        if not self.heap:
            return None
        if len(self.heap) == 1:
            priority, _, item = self.heap.pop()
            return (priority, item)
        priority, _, item = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._sift_down(0)
        return (priority, item)

    def peek(self):
        if not self.heap:
            return None
        priority, _, item = self.heap[0]
        return (priority, item)

    def __len__(self):
        return len(self.heap)

    def _sift_up(self, idx):
        parent = (idx - 1) // 2
        if idx > 0 and self.heap[idx] < self.heap[parent]:
            self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
            self._sift_up(parent)

    def _sift_down(self, idx):
        smallest = idx
        left, right = 2 * idx + 1, 2 * idx + 2
        if left < len(self.heap) and self.heap[left] < self.heap[smallest]:
            smallest = left
        if right < len(self.heap) and self.heap[right] < self.heap[smallest]:
            smallest = right
        if smallest != idx:
            self.heap[idx], self.heap[smallest] = self.heap[smallest], self.heap[idx]
            self._sift_down(smallest)
