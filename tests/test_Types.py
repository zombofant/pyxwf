# File name: test_Types.py
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

import PyXWF.Types as Types

class Typecasts(unittest.TestCase):
    def test_bool(self):
        bool = Types.Typecasts.bool

        self.assertEqual(True, bool("true"))
        self.assertEqual(True, bool("TrUe"))
        self.assertEqual(True, bool("yes"))
        self.assertEqual(True, bool("on"))
        self.assertEqual(True, bool(True))

        self.assertEqual(False, bool("false"))
        self.assertEqual(False, bool("no"))
        self.assertEqual(False, bool("off"))
        self.assertEqual(False, bool(False))

        self.assertEqual(True, bool(23))

        self.assertRaises(ValueError, bool, "foobar")
        self.assertRaises(ValueError, bool, None)

    def test_empty(self):
        empty = Types.Typecasts.empty_string

        self.assertEqual("", empty(""))
        self.assertRaises(ValueError, empty, "something")
        self.assertRaises(ValueError, empty, 23)

class EnumMap(unittest.TestCase):
    def test_mapping(self):
        mapping_dict = {
            "foo": 0,
            "bar": 1,
            "baz": 2
        }
        mapping = Types.EnumMap(mapping_dict)
        for key, value in mapping_dict.items():
            self.assertEqual(mapping(key), value)

        self.assertRaises(ValueError, mapping, None)
        self.assertRaises(ValueError, mapping, 23)


class NotNone(unittest.TestCase):
    def test_cast(self):
        not_none = Types.NotNone

        some_values = ["anything", 23, list(), object()]

        for value in some_values:
            self.assertIs(value, not_none(value))

        self.assertRaises(ValueError, not_none, None)


class DefaultForNone(unittest.TestCase):
    def test_defaulting(self):
        default = object()
        default_for_none = Types.DefaultForNone(default, Types.NotNone)

        some_values = ["anything", 23, list(), object()]

        for value in some_values:
            self.assertIs(value, default_for_none(value))

        self.assertIs(default_for_none(None), default)


class AllowBoth(unittest.TestCase):
    def test_two_mappings(self):
        mapping_dict1 = {
            "foo": 0,
            "bar": 0,
            "baz": 2,
        }
        mapping_dict2 = {
            "bar": 1
        }

        final_dict = dict(mapping_dict2)
        final_dict.update(mapping_dict1)

        allow_both = Types.AllowBoth(
            Types.EnumMap(mapping_dict1),
            Types.EnumMap(mapping_dict2)
        )

        for key, value in final_dict.items():
            self.assertIs(allow_both(key), value)

        self.assertRaises(ValueError, allow_both, "meow")


class NumericRange(unittest.TestCase):
    def test_min(self):
        numeric_range = Types.NumericRange(int, 10, None)
        self.assertEqual(numeric_range(11), 11)
        self.assertEqual(numeric_range(10), 10)
        self.assertRaises(ValueError, numeric_range, 9)

    def test_max(self):
        numeric_range = Types.NumericRange(int, None, 10)
        self.assertRaises(ValueError, numeric_range, 11)
        self.assertEqual(numeric_range(10), 10)
        self.assertEqual(numeric_range(9), 9)

    def test_range(self):
        numeric_range = Types.NumericRange(int, 9, 11)
        self.assertRaises(ValueError, numeric_range, 12)
        self.assertEqual(numeric_range(11), 11)
        self.assertEqual(numeric_range(10), 10)
        self.assertEqual(numeric_range(9), 9)
        self.assertRaises(ValueError, numeric_range, 8)


class NotEmpty(unittest.TestCase):
    def test_empty(self):
        not_empty = Types.NotEmpty
        self.assertRaises(ValueError, not_empty, "")
        self.assertRaises(ValueError, not_empty, [])
        self.assertRaises(ValueError, not_empty, ())
        self.assertRaises(ValueError, not_empty, set())
        self.assertRaises(ValueError, not_empty, {})

    def test_non_empty(self):
        not_empty = Types.NotEmpty
        s = "foo"
        l = ["bar"]
        d = {"baz": "foo"}
        self.assertIs(not_empty(s), s)
        self.assertIs(not_empty(l), l)
        self.assertIs(not_empty(d), d)

    def test_none(self):
        not_empty = Types.NotEmpty
        self.assertRaises(TypeError, not_empty, None)
