from __future__ import unicode_literals, print_function, absolute_import

import unittest, re

import PyXWF

class ReleaseVersion(unittest.TestCase):
    _develRE = re.compile("^devel-g.*$")

    @unittest.expectedFailure
    def test_isReleaseVersion(self):
        self.assertIsNone(self._develRE.match(PyXWF.__version__), "This must be fixed when releasing.")
