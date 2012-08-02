import abc, functools, time

import PyWeb.Nodes as Nodes
import PyWeb.Errors as Errors

class Cachable(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(Cachable, self).__init__()
        self._cache_lastAccess = time.time()

    def touch(self):
        self._cache_lastAccess = time.time()
        if self._cache_master is not None:
            self._cache_master._changed(self)

    def uncache(self):
        if self._cache_master is not None:
            self._cache_master._remove(self)

    @staticmethod
    def _cache_key(self):
        return self._cache_lastAccess

class SubCache(object):
    def __init__(self, cache):
        self.master = cache
        self.entries = {}
        self.reverseMap = {}

    def _kill(self, cachable):
        del self.entries[self.reverseMap[cachable]]
        del self.reverseMap[cachable]

    def getDefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def remove(self, cachable):
        self.master.remove(cachable)

    def __getitem__(self, key):
        cachable = self.entries[key]
        cachable.touch()
        return cachable

    def __setitem__(self, key, cachable):
        if key in self:
            raise KeyError("Cache key already in use: {0}".format(key))
        self.entries[key] = cachable
        self.reverseMap[cachable] = key
        
        self.master._add(cachable)
        cachable._cache_master = self.master
        cachable._cache_subcache = self

    def __delitem__(self, key):
        cachable = self.entries[key]
        cachable.uncache()

    def __contains__(self, key):
        return key in self.entries

    def __len__(self):
        return len(self.entries)
    

class Cache(object):
    def __init__(self, limit=0):
        self.subCaches = {}
        self._limit = 0
        self.Limit = limit

    def _enforceLimit(self):
        """
        Remove those entries with the oldest lastAccess from the cache.
        """
        tooMany = len(self.entries) - self.limit
        if tooMany > 0:
            overflow = self.entries[:tooMany]
            self.entries = self.entries[tooMany:]
            for entry in overflow:
                entry._cache_subcache._kill(entry)

    def _add(self, cachable):
        if self._limit:
            self.entries.append(cachable)
        
    def _changed(self, entry):
        if not self._limit:
            return
        self.entries.sort()

    def _remove(self, cachable):
        if self._limit:
            # no need to resort here
            self.entries.remove(cachable)
        cachable._cache_subcache._kill(cachable)
        del cachable._cache_master
        del cachable._cache_subcache

    def __getitem__(self, key):
        try:
            return self.subCaches[key]
        except KeyError:
            subCache = SubCache(self)
            self.subCaches[key] = subCache
            return subCache
        
    def remove(self, cachable):
        """
        Remove one entry from the cache. You can either use this or
        :meth:`CacheEntry.delete`, which does the same thing.
        """
        self._remove(cachable)

    @property
    def Limit(self):
        """
        How many cache entries are kept at max. This does not differentiate
        between different sub-caches and is a global hard-limit. If this limit
        is exceeded, old (i.e. not used for some time) entries are purged.

        Setting this limit to 0 will disable limiting.
        """
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
