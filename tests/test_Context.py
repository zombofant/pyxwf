# encoding=utf-8
from __future__ import unicode_literals

import unittest

import PyXWF.Message as Message

import tests.Mocks as Mocks

class Context(unittest.TestCase):
    def sendMessage(self, body="Foo bar", **kwargs):
        ctx = Mocks.MockedContext("/", **kwargs)
        message = Message.TextMessage(body, encoding="utf-8")
        ctx.sendResponse(message)
        return ctx

    def test_message(self):
        ctx = self.sendMessage()
        self.assertEqual(ctx.Out.getvalue(), b"""\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=utf-8

Foo bar""")

    def test_charsetDetection(self):
        ctx = self.sendMessage(acceptCharset="ascii,utf-8;q=0.9")
        self.assertEqual(ctx.Out.getvalue(), b"""\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=ascii

Foo bar""")

    def test_charsetFallback(self):
        ctx = self.sendMessage(body="äöü", acceptCharset="ascii")
        self.assertEqual(ctx.Out.getvalue(), b"""\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=utf-8

"""+"""äöü""".encode("utf-8"))

    def test_charsetDetection_complex(self):
        ctx = self.sendMessage(body="😸", acceptCharset="ascii,latin-1;q=0.9,utf-32be;q=0.8,utf-32le;q=0.8,utf-8;q=0.7")
        self.assertEqual(ctx.Out.getvalue(), b"""\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=utf-32le

"""+"""😸""".encode("utf-32le"))

