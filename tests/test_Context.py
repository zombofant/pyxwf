from __future__ import unicode_literals

import unittest

import PyXWF.Message as Message

import tests.Mocks as Mocks

class Context(unittest.TestCase):
    def sendMessage(self, **kwargs):
        ctx = Mocks.MockedContext("/", **kwargs)
        message = Message.TextMessage("Foo bar", encoding="utf-8")
        ctx.sendResponse(message)
        return ctx

    def test_message(self):
        ctx = self.sendMessage()
        self.assertEqual(ctx.Out.getvalue(), """\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=utf-8

Foo bar""")

    def test_charsetDetection(self):
        ctx = self.sendMessage(acceptCharset="ascii,utf-8;q=0.9")
        self.assertEqual(ctx.Out.getvalue(), """\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=ascii

Foo bar""")
