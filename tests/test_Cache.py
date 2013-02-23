# File name: test_Cache.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
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
