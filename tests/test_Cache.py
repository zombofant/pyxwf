from __future__ import unicode_literals

import unittest

import PyXWF.Cache as MCache

class Dummy(MCache.Cachable):
    pass

class Cache(unittest.TestCase):
    def setUp(self):
        self.cache = MCache.Cache(None)
        self.subcache = self.cache["foo"]
        self.dummies = [Dummy() for i in range(10)]
        for i, dummy in enumerate(self.dummies):
            self.subcache["d{0}".format(i)] = dummy

    def test_uncache(self):
        self.dummies[0].uncache()
        self.assertEqual(len(self.subcache), 9)

    def test_cache_limit(self):
        self.cache.Limit = 1
        self.cache.enforce_limit()
        self.assertEqual(len(self.subcache), 1)
        self.assertIn("d9", self.subcache)

    def test_propose_uncache(self):
        self.dummies[9].propose_uncache()
        self.cache.Limit = 1
        self.cache.enforce_limit()
        self.assertEqual(len(self.subcache), 1)
        self.assertIn("d8", self.subcache)

    def test_touch(self):
        self.dummies[0].touch()
        self.cache.Limit = 1
        self.cache.enforce_limit()
        self.assertEqual(len(self.subcache), 1)
        self.assertIn("d0", self.subcache)

    def tearDown(self):
        del self.cache
