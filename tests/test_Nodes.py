from __future__ import unicode_literals

import unittest

import PyXWF.Nodes as Nodes
import PyXWF.Errors as Errors

import tests.Mocks as Mocks

class Dummy(Nodes.DirectoryResolutionBehaviour):
    def _get_child(self, key):
        self._requested_key = key
        if key == "non-existing":
            return None
        return key

class DirectoryResolutionBehaviour(unittest.TestCase):
    def setUp(self):
        self.dummy = Dummy()

    def test_resolve_path(self):
        ctx = Mocks.MockedContext("/")
        paths = [
            ("", ""),
            ("foo", "foo"),
            ("bar", "bar"),
            ("bar/baz", "bar")
        ]
        for relpath, expected_key in paths:
            # this raises cause we cannot mock child nodes properly. but that
            # is fine for now
            self.assertRaises(AttributeError, self.dummy.resolve_path, ctx, relpath)
            # we can still check the key here
            self.assertEqual(self.dummy._requested_key, expected_key)

    def test_not_found(self):
        ctx = Mocks.MockedContext("/")
        self.assertRaises(Errors.HTTP.NotFound, self.dummy.resolve_path, ctx, "non-existing")

    def tearDown(self):
        del self.dummy


class Metaclass(unittest.TestCase):
    def test_callable_check(self):
        self.assertRaises(TypeError, Nodes.NodeMeta,
            b"test",
            (object, ),
            {
                "request_handlers": {
                    "GET": None
                }
            }
        )
        self.assertRaises(TypeError, Nodes.NodeMeta,
            b"test",
            (object, ),
            {
                "request_handlers": "foo"
            }
        )

    def test_dict_check(self):
        self.assertRaises(TypeError, Nodes.NodeMeta,
            b"test",
            (object, ),
            {

            }
        )

    def some_callable(self):
        pass

    def test_dict_mock(self):
        cls = Nodes.NodeMeta(b"test", (object, ), {
            "request_handlers": self.some_callable
        })
        # XXX: assertIn doesn't work here ... why?
        self.assertEqual(cls.request_handlers["GET"], self.some_callable)
