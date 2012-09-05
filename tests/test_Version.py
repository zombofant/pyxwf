from __future__ import unicode_literals, print_function, absolute_import

import unittest, re

import PyXWF

class ReleaseVersion(unittest.TestCase):
    _devel_re = re.compile("^devel-g.*$")

    @unittest.expectedFailure
    def test_is_release_version(self):
        self.assertIsNone(self._devel_re.match(PyXWF.__version__), "This must be fixed when releasing.")
