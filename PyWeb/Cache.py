import abc
import functools
import time
import heapq

import PyWeb.Nodes as Nodes
import PyWeb.Errors as Errors

class Cachable(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def LastModified(self):
        pass

@functools.total_ordering
class CacheEntry(object):
    def __init__(self, cacheObj, obj):
        self.obj = obj
        self.cacheObj = cacheObj
        self.lastAccess = time.time()

    def __eq__(self, other):
        if not isinstance(other, CacheEntry):
            return NotImplemented
        return self.lastAccess == other.lastAccess

    def __lt__(self, other):
        if not isinstance(other, CacheEntry):
            return NotImplemented
        return self.lastAccess < other.lastAccess

    def __le__(self, other):
        if not isinstance(other, CacheEntry):
            return NotImplemented
        return self.lastAccess <= other.lastAccess

    def touch(self):
        self.lastAccess = time.time()
        self.cacheObj.master.changed(self)

    @property
    def LastModified(self):
        return self.obj.LastModified

class SubCache(object):
    def __init__(self, cache):
        self.master = cache
        self.entries = {}
        self.reverseMap = {}

    def _kill(self, entry):
        del self.entries[self.reverseMap[entry]]
        del self.reverseMap[entry]

    def add(self, key, obj):
        entry = CacheEntry(self, obj)
        self.entries[key] = entry
        self.reverseMap[entry] = key
        self.master.add(entry)

    def __delitem__(self, key):
        entry = self.entries[key]
        del self.entries[key]
        del self.reverseMap[entry]
        self.master.remove(entry)

    def get(self, key, ifModifiedSince=None):
        entry = self[key]
        if ifModifiedSince is not None:
            if entry.LastModified <= ifModifiedSince:
                raise Errors.NotModified()
        return entry.obj

    def __getitem__(self, key):
        entry = self.entries[key]
        entry.touch()
        return entry

    def __contains__(self, key):
        return key in self.entries

    def getDefault(self, key, default, ifModifiedSince=None):
        try:
            return self.get(key, ifModifiedSince=ifModifiedSince)
        except KeyError:
            return default

class Cache(object):
    def __init__(self, limit=0):
        self.subCaches = {}
        self._limit = 0
        self.Limit = limit

    def __getitem__(self, key):
        try:
            return self.subCaches[key]
        except KeyError:
            cache = SubCache(self)
            self.subCaches[key] = cache
            return cache

    def specializedSubCache(self, key, cls, *args, **kwargs):
        if key in self.subCaches:
            raise KeyError("{0} is already in use.".format(key))
        cache = cls(self, *args, **kwargs)
        self.subCaches[key] = cache
        return cache

    def _enforceLimit(self):
        tooMany = len(self.heap) - self.limit
        while tooMany > 0:
            entry = heapq.heappop(self.heap)
            entry.cache._kill(entry)
            tooMany -= 1

    def add(self, entry):
        if not self._limit:
            return
        heapq.heappush(self.heap, entry)
        self._enforceLimit()
        
    def changed(self, entry):
        if not self._limit:
            return
        heapq.heapify(self.heap)

    def remove(self, entry):
        if not self._limit:
            return
        self.heap(remove, entry)
        heapq.heapify(self.heap)

    @property
    def Limit(self):
        return self.limit

    @Limit.setter
    def Limit(self, value):
        if value is None:
            value = 0
        value = int(value)
        if value == self._limit:
            return
        if value < 0:
            raise ValueError("Cache limit must be non-negative.")
        
        if value == 0:
            del self.heap
        else:
            self.heap = []
            for cache in self.subCaches.viewvalues():
                self.heap.extend(cache.entries.viewvalues())
            heapq.heapify(self.heap)
            self._enforceLimit()
        self._limit = value