__version__ = "surrogate"

class sortedlist(list):
    def __init__(self, iterable=[], key=lambda x: x):
        super(sortedlist, self).__init__(iterable)
        self._key = key

    def add(self, obj):
        super(sortedlist, self).append(obj)
        self.sort(key=self._key)
