# encoding=utf-8
from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Context as MContext
import PyXWF.Message as Message
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS

import tests.Mocks as Mocks

class Context(unittest.TestCase):
    def send_message(self, body="Foo bar", **kwargs):
        ctx = Mocks.MockedContext("/", **kwargs)
        message = Message.TextMessage(body, encoding="utf-8")
        ctx.send_response(message)
        return ctx

    def test_message(self):
        ctx = self.send_message()
        self.assertMultiLineEqual(ctx.Out.getvalue(), b"""\
200 OK
content-type: text/plain; charset=utf-8
vary: host

Foo bar""")

    def test_charset_detection(self):
        ctx = self.send_message(accept_charset="ascii,utf-8;q=0.9")
        self.assertMultiLineEqual(ctx.Out.getvalue(), b"""\
200 OK
content-type: text/plain; charset=ascii
vary: host

Foo bar""")

    def test_charset_iso_inclusion(self):
        ctx = self.send_message(body="äöü", accept_charset="ascii")
        self.assertMultiLineEqual(ctx.Out.getvalue(), b"""\
200 OK
content-type: text/plain; charset=iso-8859-1
vary: host

"""+"""äöü""".encode("iso-8859-1"))

    def test_charset_no_fallback(self):
        self.assertRaises(Errors.NotAcceptable, self.send_message, body="äöü", accept_charset="ascii,*;q=0")

    def test_charset_detection_complex(self):
        ctx = self.send_message(body="😸", accept_charset="ascii,latin-1;q=0.9,utf-32be;q=0.8,utf-32le;q=0.8,utf-8;q=0.7,*;q=0")
        self.assertMultiLineEqual(ctx.Out.getvalue(), b"""\
200 OK
content-type: text/plain; charset=utf-32le
vary: host

"""+"""😸""".encode("utf-32le"))

    def test_xhtml_charset(self):
        ctx = Mocks.MockedContext("/", accept="")
        message = Message.XHTMLMessage(NS.XHTML("html"))
        ctx.send_response(message)

        self.assertMultiLineEqual(ctx.Out.getvalue(), b"""\
200 OK
content-type: application/xhtml+xml; charset=utf-8
vary: host

"""+message.get_encoded_body())
