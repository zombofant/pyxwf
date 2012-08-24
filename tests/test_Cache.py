from __future__ import unicode_literals

import unittest

import PyWeb.Cache as MCache

class Dummy(MCache.Cachable):
    pass

class Cache(unittest.TestCase):
    def setUp(self):
        self.cache = MCache.Cache(None)
        self.subCache = self.cache["foo"]
        self.dummies = [Dummy() for i in range(10)]
        for i, dummy in enumerate(self.dummies):
            self.subCache["d{0}".format(i)] = dummy

    def test_uncache(self):
        self.dummies[0].uncache()
        self.assertEqual(len(self.subCache), 9)

    def test_cacheLimit(self):
        self.cache.Limit = 1
        self.cache.enforceLimit()
        self.assertEqual(len(self.subCache), 1)
        self.assertIn("d9", self.subCache)

    def test_proposeUncache(self):
        self.dummies[9].proposeUncache()
        self.cache.Limit = 1
        self.cache.enforceLimit()
        self.assertEqual(len(self.subCache), 1)
        self.assertIn("d8", self.subCache)

    def test_touch(self):
        self.dummies[0].touch()
        self.cache.Limit = 1
        self.cache.enforceLimit()
        self.assertEqual(len(self.subCache), 1)
        self.assertIn("d0", self.subCache)

    def tearDown(self):
        del self.cache
