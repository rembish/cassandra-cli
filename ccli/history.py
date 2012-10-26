class History(list):
    def __init__(self):
        super(History, self).__init__()
        self.position = 0

    def append(self, element):
        if not element:
            return
        if element in self:
            self.remove(element)

        super(History, self).append(element)
        self.position = len(self)

    def up(self):
        self.position = max(self.position - 1, 0)
        if not self:
            return None
        return self[self.position]

    def down(self):
        self.position = min(self.position + 1, len(self))
        if len(self) <= self.position:
            return None
        return self[self.position]

    def search(self, s): # TODO we need more power
        for e in self[::-1]:
            if e.startswith(s):
                return e
        return None