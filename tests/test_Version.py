# File name: test_Version.py
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
from __future__ import unicode_literals, print_function, absolute_import

import unittest, re

import PyXWF

class ReleaseVersion(unittest.TestCase):
    _devel_re = re.compile("^devel-g.*$")

    @unittest.expectedFailure
    def test_is_release_version(self):
        self.assertIsNone(self._devel_re.match(PyXWF.__version__), "This must be fixed when releasing.")
