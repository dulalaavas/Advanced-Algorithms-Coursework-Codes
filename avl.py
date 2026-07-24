class AVLNode:
    def __init__(self, key, data):
        self.key = key
        self.data = data
        self.left = None
        self.right = None
        self.height = 1


class AVLTree:
    """Self-balancing AVL tree. Same API as BST so the benchmark treats both
    uniformly. Rotation is chosen by balance factor. Assumes unique keys."""
    def __init__(self):
        self.root = None

    def insert(self, key, data):
        self.root = self._insert(self.root, key, data)

    def _insert(self, node, key, data):
        if not node:
            return AVLNode(key, data)
        if key < node.key:
            node.left = self._insert(node.left, key, data)
        elif key > node.key:
            node.right = self._insert(node.right, key, data)
        else:
            node.data = data
            return node
        node.height = 1 + max(self._h(node.left), self._h(node.right))
        return self._rebalance(node)

    def search(self, key):
        node = self.root
        while node:
            if key == node.key:
                return node.data
            node = node.left if key < node.key else node.right
        return None

    def delete(self, key):
        self.root = self._delete(self.root, key)

    def _delete(self, node, key):
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            succ = node.right
            while succ.left:
                succ = succ.left
            node.key = succ.key
            node.data = succ.data
            node.right = self._delete(node.right, succ.key)
        node.height = 1 + max(self._h(node.left), self._h(node.right))
        return self._rebalance(node)

    def _rebalance(self, node):
        balance = self._balance(node)
        if balance > 1:
            if self._balance(node.left) < 0:
                node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        if balance < -1:
            if self._balance(node.right) > 0:
                node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        return node

    def _left_rotate(self, z):
        y = z.right
        z.right = y.left
        y.left = z
        z.height = 1 + max(self._h(z.left), self._h(z.right))
        y.height = 1 + max(self._h(y.left), self._h(y.right))
        return y

    def _right_rotate(self, z):
        y = z.left
        z.left = y.right
        y.right = z
        z.height = 1 + max(self._h(z.left), self._h(z.right))
        y.height = 1 + max(self._h(y.left), self._h(y.right))
        return y

    def _h(self, node):
        return node.height if node else 0

    def _balance(self, node):
        return self._h(node.left) - self._h(node.right) if node else 0

    def height(self):
        return self._h(self.root)
