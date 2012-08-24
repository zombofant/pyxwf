from __future__ import unicode_literals

import unittest

import PyXWF.Nodes as Nodes
import PyXWF.Errors as Errors

import tests.Mocks as Mocks

class Dummy(Nodes.DirectoryResolutionBehaviour):
    def _getChildNode(self, key):
        self._requestedKey = key
        if key == "non-existing":
            return None
        return key

class DirectoryResolutionBehaviour(unittest.TestCase):
    def setUp(self):
        self.dummy = Dummy()

    def test_resolvePath(self):
        ctx = Mocks.MockedContext("/")
        paths = [
            ("", ""),
            ("foo", "foo"),
            ("bar", "bar"),
            ("bar/baz", "bar")
        ]
        for relPath, expectedKey in paths:
            # this raises cause we cannot mock child nodes properly. but that
            # is fine for now
            self.assertRaises(AttributeError, self.dummy.resolvePath, ctx, relPath)
            # we can still check the key here
            self.assertEqual(self.dummy._requestedKey, expectedKey)

    def test_notFound(self):
        ctx = Mocks.MockedContext("/")
        self.assertRaises(Errors.HTTP.NotFound, self.dummy.resolvePath, ctx, "non-existing")

    def tearDown(self):
        del self.dummy


class Metaclass(unittest.TestCase):
    def test_callableCheck(self):
        self.assertRaises(TypeError, Nodes.NodeMeta,
            b"test",
            (object, ),
            {
                "requestHandlers": {
                    "GET": None
                }
            }
        )
        self.assertRaises(TypeError, Nodes.NodeMeta,
            b"test",
            (object, ),
            {
                "requestHandlers": "foo"
            }
        )

    def test_dictCheck(self):
        self.assertRaises(TypeError, Nodes.NodeMeta,
            b"test",
            (object, ),
            {

            }
        )

    def someCallable(self):
        pass

    def test_dictMock(self):
        cls = Nodes.NodeMeta(b"test", (object, ), {
            "requestHandlers": self.someCallable
        })
        # XXX: assertIn doesn't work here ... why?
        self.assertEqual(cls.requestHandlers["GET"], self.someCallable)
