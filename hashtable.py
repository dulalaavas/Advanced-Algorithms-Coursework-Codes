class _Entry:
    __slots__ = ('key', 'data')
    def __init__(self, key, data):
        self.key = key
        self.data = data


class HashTable:
    """Separate-chaining hash table with prime capacity. Doubles to the next
    prime when load factor exceeds 0.7 to keep operations O(1) average."""
    _INITIAL_CAPACITY = 11
    _LOAD_FACTOR_THRESHOLD = 0.7

    def __init__(self):
        self._capacity = self._INITIAL_CAPACITY
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0

    @staticmethod
    def _is_prime(n):
        if n < 2:
            return False
        if n in (2, 3):
            return True
        if n % 2 == 0:
            return False
        i = 3
        while i * i <= n:
            if n % i == 0:
                return False
            i += 2
        return True

    def _next_prime(self, n):
        candidate = n if n % 2 else n + 1
        while not self._is_prime(candidate):
            candidate += 2
        return candidate

    def _hash(self, key):
        return hash(key) % self._capacity

    def insert(self, key, data):
        if self._size / self._capacity >= self._LOAD_FACTOR_THRESHOLD:
            self._resize()
        bucket = self._buckets[self._hash(key)]
        for entry in bucket:
            if entry.key == key:
                entry.data = data
                return
        bucket.append(_Entry(key, data))
        self._size += 1

    def search(self, key):
        for entry in self._buckets[self._hash(key)]:
            if entry.key == key:
                return entry.data
        return None

    def delete(self, key):
        bucket = self._buckets[self._hash(key)]
        for i, entry in enumerate(bucket):
            if entry.key == key:
                bucket.pop(i)
                self._size -= 1
                return True
        return False

    def _resize(self):
        old_buckets = self._buckets
        self._capacity = self._next_prime(self._capacity * 2)
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0
        for bucket in old_buckets:
            for entry in bucket:
                self.insert(entry.key, entry.data)

    def load_factor(self):
        return self._size / self._capacity

    def __len__(self):
        return self._size

    def max_chain_length(self):
        """Worst-case bucket size observed (diagnostic for the report)."""
        return max((len(b) for b in self._buckets), default=0)
