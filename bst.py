from typing import Optional

class BSTNode:
    def __init__(self, key, data):
        self.key = key
        self.data = data
        self.left: Optional["BSTNode"] = None
        self.right: Optional["BSTNode"] = None

class BST:
    """Plain (unbalanced) BST. Insert/search/delete/height are all iterative to avoid recursion-depth failures."""
    def __init__(self):
        self.root = None

    def insert(self, key, data):
        if self.root is None:
            self.root = BSTNode(key, data)
            return
        node = self.root
        while True:
            if key < node.key:
                if node.left is None:
                    node.left = BSTNode(key, data)
                    return
                node = node.left
            elif key > node.key:
                if node.right is None:
                    node.right = BSTNode(key, data)
                    return
                node = node.right
            else:
                node.data = data
                return

    def search(self, key):
        node = self.root
        while node:
            if key == node.key:
                return node.data
            node = node.left if key < node.key else node.right
        return None

    def delete(self, key):
        parent = None
        node = self.root
        while node is not None and node.key != key:
            parent = node
            node = node.left if key < node.key else node.right
        if node is None:
            return
        # Two children: copy in-order successor into node, then delete the successor instead.
        if node.left is not None and node.right is not None:
            succ_parent = node
            succ = node.right
            while succ.left is not None:
                succ_parent = succ
                succ = succ.left
            node.key = succ.key
            node.data = succ.data
            parent = succ_parent
            node = succ
        # 0 or 1 child: splice node out.
        child = node.left if node.left is not None else node.right
        if parent is None:
            self.root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child

    def height(self):
        if self.root is None:
            return 0
        max_depth = 0
        stack = [(self.root, 1)]
        while stack:
            node, depth = stack.pop()
            max_depth = max(max_depth, depth)
            if node.left:
                stack.append((node.left, depth + 1))
            if node.right:
                stack.append((node.right, depth + 1))
        return max_depth
