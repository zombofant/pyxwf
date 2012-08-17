"""
Caching framework for PyWeb. This is probably not as mature as we may need it
in the future, but it provides basic means for caching resources used by the
PyWeb instance.

It may, in the future, also be used to cache complete rendered pages.
"""

import abc, functools, time, os

import PyWeb.Nodes as Nodes
import PyWeb.Errors as Errors
import PyWeb.utils as utils

class Cachable(object):
    """
    Represents an object which can reside in a cache. This class defines the
    interface neccessary for a cache entry to work properly. The following
    attributes are used (and reserved by) the caching framework on Cachables:

    * `_cache_lastAccess` -- timestamp of last access of the object via the
      cache. This is used as a metric of when an entry can be uncached if limits
      are reached.
    * `_cache_master` -- The :cls:`Cache` instance holding the object.
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
    The big master cache (:cls:`Cache` instance) is subdivided into smaller
    parts, :cls:`SubCache` instances, which can be thought of namespaces inside
    the cache.

    They're used to separate different kinds of cachable objects, which can be
    handled by different `SubCache`-derived classes. See
    :cls:`FileSourcedCache` as an example for optimizations possible using
    this.

    SubCaches provide dictionary-like access to cachables, associating *keys*
    to the cachables. An object can be added to the cache by simply assigning
    a key to it. Objects can also be uncached by using the `del` operator. The
    `in` operator and the `len` function work properly.
    """

    def __init__(self, cache):
        self.master = cache
        self.entries = {}
        self.reverseMap = {}

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
        try:
            return self[key]
        except KeyError:
            return default

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

    def getLastModified(self, key):
        """
        Return the datetime representing the last modification of the cached
        content. The default implementation requests the cached element from
        the cache and queries the LastModified property.

        Derived classes may (and should!) provide mechanisms which can query
        the LastModified timestamp without completely loading an object.
        """
        return self[key].LastModified

    def update(self, key):
        """
        Call `update()` on the cache entry referenced by *key*, but only if
        *key* references a valid entry. Otherwise, nothing happens. This is
        used to ensure that cached entries are reloaded if they wouldn't be
        reloaded anyways on the next access.
        """
        try:
            entry = self.entries[key]
        except KeyError:
            return
        entry.update()


class Cache(object):
    """
    Master object representing a full application cache. Objects are not
    directly stored in the :cls:`Cache` instance but in sub-caches. The
    :cls:`Cache` object provides dictionary-like access to sub caches. If no
    cache is associated with a certain key, a new raw :cls:`SubCache` is created
    for that key.

    Specialized sub caches can be created using :meth:`specializedSubcache`.
    """
    def __init__(self, limit=0):
        self.subCaches = {}
        self._limit = 0
        self.Limit = limit

    def _add(self, cachable):
        """
        Add a cachable. Do not call this directly. Only used for bookkeeping.
        """
        if self._limit:
            self.entries.append(cachable)

    def _changed(self, entry):
        """
        Resort the container keeping track of all entries to enforce cache
        limits.
        """
        if not self._limit:
            return
        self.entries.sort()

    def _remove(self, cachable):
        """
        Remove a cachable from the cache.
        """
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

    def __delitem__(self, key):
        cache = self.subCaches[key]
        for entry in cache.entries.values():
            entry.uncache()
        del self.subCaches[key]

    def specializedCache(self, key, cls, *args, **kwargs):
        """
        Create a specialized subcache using the given class *cls* at the given
        *key*. Further arguments and keyword arguments are passed to the
        constructor of *cls*.

        Return the new *cls* instance.
        """
        cache = cls(self, *args, **kwargs)
        if key in self.subCaches:
            raise KeyError("SubCache key already in use: {0}".format(key))
        self.subCaches[key] = cache
        return cache

    def remove(self, cachable):
        """
        Remove one entry from the cache. You can either use this or
        :meth:`CacheEntry.delete`, which does the same thing.
        """
        self._remove(cachable)

    def enforceLimit(self):
        """
        Remove those entries with the oldest lastAccess from the cache.
        """
        if not self._limit:
            return
        tooMany = len(self.entries) - self._limit
        if tooMany > 0:
            overflow = self.entries[:tooMany]
            self.entries = self.entries[tooMany:]
            for entry in overflow:
                entry._cache_subcache._kill(entry)

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
            self.entries = []
            for cache in self.subCaches.viewvalues():
                self.entries.extend(cache.entries.viewvalues())
            self.entries.sort()
            self.enforceLimit()
        self._limit = value


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
        In contrast to the implementation given in :cls:`SubCache`, this
        implementation uses the timestamp of last modification of the file
        referenced by *key*. This implies that a resource is not neccessarily
        loaded (or even loadable!) even if a LastModified can be retrieved
        successfully.
        """
        return utils.fileLastModified(self._transformKey(key))

    def update(self, key):
        super(FileSourcedCache, self).update(self._transformKey(key))

    __setitem__ = None
