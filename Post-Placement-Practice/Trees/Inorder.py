class Node:
    def __init__(self,data):
        self.data = data
        self.left = None
        self.right = None


def InorderTraversal(root):
    if root is None:
        return []
    
    stack = []
    result = []

    current = root

    while current is None or stack:
        # Go as far left as possible
        while current is not None:
            stack.append(current)
            current = current.left
        
        # Process the leftmost node
        current = stack.pop()
        result.append(current.data)

        current = current.right
    
    return result

# Driver Code
if __name__ == "__main__":

    #        1
    #       / \
    #      2   3
    #     / \   \
    #    4   5   6

    root = Node(1)
    root.left = Node(2)
    root.right = Node(3)

    root.left.left = Node(4)
    root.left.right = Node(5)

    root.right.right = Node(6)

    result = InorderTraversal(root)

    print(" -> ".join(map(str, result)))