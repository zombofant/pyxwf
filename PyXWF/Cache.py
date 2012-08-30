"""
Caching framework for PyXWF. This is probably not as mature as we may need it
in the future, but it provides basic means for caching resources used by the
PyXWF instance.

It may, in the future, also be used to cache complete rendered pages.
"""

import abc, functools, time, os, operator

from PyXWF.utils import threading
import PyXWF.Nodes as Nodes
import PyXWF.Errors as Errors
import PyXWF.utils as utils

class Cachable(object):
    """
    Represents an object which can reside in a cache. This class defines the
    interface neccessary for a cache entry to work properly. The following
    attributes are used (and reserved by) the caching framework on Cachables:

    * `_cache_lastAccess` -- timestamp of last access of the object via the
      cache. This is used as a metric of when an entry can be uncached if limits
      are reached.
    * `_cache_master` -- The :class:`Cache` instance holding the object.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(Cachable, self).__init__()
        self._cache_lastAccess = time.time()
        self._cache_master = None

    def touch(self):
        """
        Set the internal timestamp of last use to the current timestamp. This
        will also inform the master (if known) of the changed value for uncache
        metrics.
        """
        self._cache_lastAccess = time.time()
        if self._cache_master is not None:
            self._cache_master._changed(self)

    def uncache(self):
        """
        Remove the object from the cache it is associated to.
        """
        if self._cache_master is not None:
            self._cache_master._remove(self)

    def proposeUncache(self):
        """
        Set the timestamp of last use in the past so that uncaching of this
        object in case of reached limits is more likely than for other objects.
        """
        # it must be something which is definetly in the past (a date which is
        # easier to find than a date which is definetly in the future. Greetings
        # to MTA folks).
        self._cache_lastAccess = 0

    @staticmethod
    def _cache_key(self):
        return self._cache_lastAccess

class SubCache(object):
    """
    The big master cache (:class:`Cache` instance) is subdivided into smaller
    parts, :class:`SubCache` instances, which can be thought of namespaces inside
    the cache.

    They're used to separate different kinds of cachable objects, which can be
    handled by different `SubCache`-derived classes. See
    :class:`FileSourcedCache` as an example for optimizations possible using
    this.

    SubCaches provide dictionary-like access to cachables, associating *keys*
    to the cachables. An object can be added to the cache by simply assigning
    a key to it. Objects can also be uncached by using the `del` operator. The
    `in` operator and the `len` function work properly.
    """

    def __init__(self, cache):
        self.site = cache.site
        self.master = cache
        self.entries = {}
        self.reverseMap = {}
        self._lookupLock = threading.RLock()

    def _kill(self, cachable):
        """
        Delete a cache entry from the subcache. Do not call this method. Uncache
        entries using :meth:`remove()`, :meth:`Cachable.uncache()` or
        :meth:`Cache.remove()`.
        """
        del self.entries[self.reverseMap[cachable]]
        del self.reverseMap[cachable]

    def getDefault(self, key, default=None):
        """
        Try to get an object from the cache and return *default* (defaults to
        ``None``) if no object is associated with *key*.
        """
        self._lookupLock.acquire()
        try:
            try:
                return self[key]
            except KeyError:
                return default
        finally:
            self._lookupLock.release()

    def remove(self, cachable):
        """
        Remove a cachable from the Cache.
        """
        self.master.remove(cachable)

    def __getitem__(self, key):
        cachable = self.entries[key]
        cachable.touch()
        return cachable

    def __setitem__(self, key, cachable):
        self._lookupLock.acquire()
        try:
            if key in self:
                raise KeyError("Cache key already in use: {0}".format(key))
            self.entries[key] = cachable
            self.reverseMap[cachable] = key

            self.master._add(cachable)
            cachable._cache_master = self.master
            cachable._cache_subcache = self
        finally:
            self._lookupLock.release()

    def __delitem__(self, key):
        self._lookupLock.acquire()
        try:
            cachable = self.entries[key]
            cachable.uncache()
        finally:
            self._lookupLock.release()

    def __contains__(self, key):
        self._lookupLock.acquire()
        try:
            return key in self.entries
        finally:
            self._lookupLock.release()

    def __len__(self):
        return len(self.entries)

    def getLastModified(self, key):
        """
        Return the datetime representing the last modification of the cached
        content. The default implementation requests the cached element from
        the cache and queries the LastModified property.

        Derived classes may (and should!) provide mechanisms which can query
        the LastModified timestamp without completely loading an object.
        """
        self._lookupLock.acquire()
        try:
            return self[key].LastModified
        finally:
            self._lookupLock.release()

    def update(self, key):
        """
        Call `update()` on the cache entry referenced by *key*, but only if
        *key* references a valid entry. Otherwise, nothing happens. This is
        used to ensure that cached entries are reloaded if they wouldn't be
        reloaded anyways on the next access.
        """
        self._lookupLock.acquire()
        try:
            try:
                entry = self.entries[key]
            except KeyError:
                return
        finally:
            self._lookupLock.release()
        entry.threadSafeUpdate()


class Cache(object):
    """
    Master object representing a full application cache. Objects are not
    directly stored in the :class:`Cache` instance but in sub-caches. The
    :class:`Cache` object provides dictionary-like access to sub caches. If no
    cache is associated with a certain key, a new raw :class:`SubCache` is created
    for that key.

    Specialized sub caches can be created using :meth:`specializedSubcache`.
    """
    def __init__(self, site, limit=0):
        self._lookupLock = threading.RLock()
        self._limitLock = threading.RLock()
        self.site = site
        self.subCaches = {}
        self._limit = 0
        self.Limit = limit

    def _add(self, cachable):
        """
        Add a cachable. Do not call this directly. Only used for bookkeeping.
        """
        self._limitLock.acquire()
        try:
            if self._limit:
                self.entries.append(cachable)
        finally:
            self._limitLock.release()

    def _changed(self, entry):
        """
        Resort the container keeping track of all entries to enforce cache
        limits.
        """
        self._limitLock.acquire()
        try:
            if not self._limit:
                return
            self.entries.sort()
        finally:
            self._limitLock.release()

    def _remove(self, cachable):
        """
        Remove a cachable from the cache. This already holds the limit lock.
        """
        if self._limit:
            # no need to resort here
            self.entries.remove(cachable)
        cachable._cache_subcache._kill(cachable)
        del cachable._cache_master
        del cachable._cache_subcache

    def __getitem__(self, key):
        self._lookupLock.acquire()
        try:
            try:
                return self.subCaches[key]
            except KeyError:
                subCache = SubCache(self)
                self.subCaches[key] = subCache
                return subCache
        finally:
            self._lookupLock.release()

    def __delitem__(self, key):
        self._lookupLock.acquire()
        try:
            cache = self.subCaches[key]
            for entry in cache.entries.values():
                entry.uncache()
            del self.subCaches[key]
        finally:
            self._lookupLock.release()

    def specializedCache(self, key, cls, *args, **kwargs):
        """
        Create a specialized subcache using the given class *cls* at the given
        *key*. Further arguments and keyword arguments are passed to the
        constructor of *cls*.

        Return the new *cls* instance.
        """
        cache = cls(self, *args, **kwargs)
        self._lookupLock.acquire()
        try:
            if key in self.subCaches:
                raise KeyError("SubCache key already in use: {0}".format(key))
            self.subCaches[key] = cache
        finally:
            self._lookupLock.release()
        return cache

    def remove(self, cachable):
        """
        Remove one entry from the cache. You can either use this or
        :meth:`CacheEntry.delete`, which does the same thing.
        """
        self._limitLock.acquire()
        try:
            self._remove(cachable)
        finally:
            self._limitLock.release()

    def enforceLimit(self):
        """
        Remove those entries with the oldest lastAccess from the cache.
        """
        self._limitLock.acquire()
        try:
            if not self._limit:
                return
            tooMany = len(self.entries) - self._limit
            if tooMany > 0:
                overflow = self.entries[:tooMany]
                self.entries = self.entries[tooMany:]
                for entry in overflow:
                    entry._cache_subcache._kill(entry)
        finally:
            self._limitLock.release()

    @property
    def Limit(self):
        """
        How many cache entries are kept at max. This does not differentiate
        between different sub-caches and is a global hard-limit. If this limit
        is exceeded, old (i.e. not used for some time) entries are purged.

        Setting this limit to 0 will disable limiting.
        """
        self._limitLock.acquire()
        try:
            return self.limit
        finally:
            self._limitLock.release()

    @Limit.setter
    def Limit(self, value):
        self._limitLock.acquire()
        try:
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
                self.entries = []
                for cache in self.subCaches.viewvalues():
                    self.entries.extend(cache.entries.viewvalues())
                self.entries.sort(key=operator.attrgetter("_cache_lastAccess"))
                self.enforceLimit()
            self._limit = value
        finally:
            self._limitLock.release()


class FileSourcedCache(SubCache):
    """
    This is an abstract baseclass for caches which are backed by files on the
    file system. The file names are used as keys relative to a given root
    directory *rootPath*.

    A deriving class has to implement the *_load* method which is called if a
    file accessed through this cache is not available in the cache.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, master, rootPath):
        super(FileSourcedCache, self).__init__(master)
        self.rootPath = rootPath

    @abc.abstractmethod
    def _load(self, path):
        """
        Derived classes have to implement this method. It must return the loaded
        object behind *path* or raise.
        """

    def _transformKey(self, key):
        return os.path.join(self.rootPath, key)

    def __getitem__(self, key, **kwargs):
        path = self._transformKey(key)
        try:
            return super(FileSourcedCache, self).__getitem__(path)
        except KeyError:
            obj = self._load(path, **kwargs)
            super(FileSourcedCache, self).__setitem__(path, obj)
            return obj

    def getLastModified(self, key):
        """
        In contrast to the implementation given in :class:`SubCache`, this
        implementation uses the timestamp of last modification of the file
        referenced by *key*. This implies that a resource is not neccessarily
        loaded (or even loadable!) even if a LastModified can be retrieved
        successfully.
        """
        return utils.fileLastModified(self._transformKey(key))

    def update(self, key):
        super(FileSourcedCache, self).update(self._transformKey(key))

    __setitem__ = None
