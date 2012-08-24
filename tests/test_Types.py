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
        empty = Types.Typecasts.emptyString

        self.assertEqual("", empty(""))
        self.assertRaises(ValueError, empty, "something")
        self.assertRaises(ValueError, empty, 23)

class EnumMap(unittest.TestCase):
    def test_mapping(self):
        mappingDict = {
            "foo": 0,
            "bar": 1,
            "baz": 2
        }
        mapping = Types.EnumMap(mappingDict)
        for key, value in mappingDict.items():
            self.assertEqual(mapping(key), value)

        self.assertRaises(ValueError, mapping, None)
        self.assertRaises(ValueError, mapping, 23)


class NotNone(unittest.TestCase):
    def test_cast(self):
        notNone = Types.NotNone

        someValues = ["anything", 23, list(), object()]

        for value in someValues:
            self.assertIs(value, notNone(value))

        self.assertRaises(ValueError, notNone, None)


class DefaultForNone(unittest.TestCase):
    def test_defaulting(self):
        default = object()
        defaultForNone = Types.DefaultForNone(default, Types.NotNone)

        someValues = ["anything", 23, list(), object()]

        for value in someValues:
            self.assertIs(value, defaultForNone(value))

        self.assertIs(defaultForNone(None), default)


class AllowBoth(unittest.TestCase):
    def test_twoMappings(self):
        mappingDict1 = {
            "foo": 0,
            "bar": 0,
            "baz": 2,
        }
        mappingDict2 = {
            "bar": 1
        }

        finalDict = dict(mappingDict2)
        finalDict.update(mappingDict1)

        allowBoth = Types.AllowBoth(
            Types.EnumMap(mappingDict1),
            Types.EnumMap(mappingDict2)
        )

        for key, value in finalDict.items():
            self.assertIs(allowBoth(key), value)

        self.assertRaises(ValueError, allowBoth, "meow")


class NumericRange(unittest.TestCase):
    def test_min(self):
        numericRange = Types.NumericRange(int, 10, None)
        self.assertEqual(numericRange(11), 11)
        self.assertEqual(numericRange(10), 10)
        self.assertRaises(ValueError, numericRange, 9)

    def test_max(self):
        numericRange = Types.NumericRange(int, None, 10)
        self.assertRaises(ValueError, numericRange, 11)
        self.assertEqual(numericRange(10), 10)
        self.assertEqual(numericRange(9), 9)

    def test_range(self):
        numericRange = Types.NumericRange(int, 9, 11)
        self.assertRaises(ValueError, numericRange, 12)
        self.assertEqual(numericRange(11), 11)
        self.assertEqual(numericRange(10), 10)
        self.assertEqual(numericRange(9), 9)
        self.assertRaises(ValueError, numericRange, 8)
