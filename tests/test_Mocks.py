# File name: test_Mocks.py
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
# this is quite meta
from __future__ import unicode_literals

import os, unittest

import Mocks

class MockFSLocation(unittest.TestCase):
    def setUp(self):
        self.location = Mocks.MockFSLocation()

    def test_dirs(self):
        self.assertTrue(os.path.isdir(self.location.Root))

    def test_close(self):
        self.location.close()
        self.assertRaises(ValueError, getattr, self.location, "Root")

    def test___call__(self):
        path = "foo/bar"
        self.assertEqual(os.path.join(self.location.Root, path), self.location(path))

    def test_open(self):
        somefile = "foo.bar"
        f = self.location.open(somefile, "w")
        f.close()
        self.assertTrue(os.path.isfile(self.location(somefile)))

    def tearDown(self):
        self.location.close()
