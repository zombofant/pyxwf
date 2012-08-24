from __future__ import unicode_literals

import unittest

import PyWeb.Message as Message

import tests.Mocks as Mocks

class Context(unittest.TestCase):
    def sendMessage(self):
        ctx = Mocks.MockedContext("/")
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
