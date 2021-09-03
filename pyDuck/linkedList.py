class LinkedList:
    @staticmethod
    def from_list(ls):
        linked_list = LinkedList()
        if len(ls) == 0: return linked_list
        first = ls.pop(0)
        linked_list.prepend(first)
        for elem in ls:
            linked_list.append(elem)
        ls.insert(0, first)
        return linked_list

    def __init__(self, head=None, tail=None):
        self.head = head
        self.tail = tail

    def prepend(self, data):
        tempNode = LinkedList(data)
        tempNode.tail = self.head
        self.head = tempNode
        del tempNode

    def append(self, data):
        start = self.head
        tempNode = LinkedList(data)
        while start.tail:
            start = start.tail
        start.tail = tempNode
        del tempNode

    def __str__(self):
        start = self.head
        s = ""
        while start:
            s += str(start.head)
            start = start.tail
            if start:
                s += ", "
        return "LinkedList([" + s + "])"

    def remove(self, item):
        start = self.head
        previous = None
        found = False

        while not found:
            if start.head == item:
                found = True
            else:
                previous = start
                start = start.tail

        if previous is None:
            self.head = start.tail
        else:
            previous.setLink(start.tail)
        return found

    def __iter__(self):
        start = self.head
        size = 0
        while start:
            yield start.head
            start = start.tail

    # @property
    def size(self):
        i = 0
        for _ in self:
            i += 1
        return i