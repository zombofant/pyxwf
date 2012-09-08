# encoding=utf-8
from __future__ import unicode_literals

import unittest
import base64
import logging

from PyXWF.utils import ET
import PyXWF.Context as MContext
import PyXWF.Message as Message
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS

import tests.Mocks as Mocks

class Cookie(unittest.TestCase):
    def test_encode_value_exact(self):
        message = b"foobar"
        encoded = MContext.Cookie.encode_value(message)
        self.assertEqual(encoded, base64.urlsafe_b64encode(message))
        self.assertIsInstance(encoded, str)

    def test_encode_value_stripped(self):
        message = b"foob"
        encoded = MContext.Cookie.encode_value(message)
        self.assertEqual(encoded, base64.urlsafe_b64encode(message)[:-2])
        self.assertIsInstance(encoded, str)

    def test_encode_value_unicode(self):
        message = "äöü"
        encoded = MContext.Cookie.encode_value(message)
        self.assertEqual(encoded, base64.urlsafe_b64encode(message.encode("utf-8")))
        self.assertIsInstance(encoded, str)

    def test_decode_value_exact(self):
        encoded = b"Zm9vYmFy"
        message = MContext.Cookie.decode_value(encoded)
        self.assertEqual("foobar", message)
        self.assertIsInstance(message, unicode)

    def test_decode_value_stripped(self):
        encoded = b"Zm9vYg"
        message = MContext.Cookie.decode_value(encoded)
        self.assertEqual("foob", message)
        self.assertIsInstance(message, unicode)

    def test_encode_decode_roundtrip(self):
        message = "äöü"
        encoded = MContext.Cookie.encode_value(message)
        roundtripped = MContext.Cookie.decode_value(encoded)
        self.assertEqual(roundtripped, message)

    def test_from_cookie_header_unicode_error(self):
        cookie_av = "foo={0}".format(MContext.Cookie.encode_value("bar"))
        self.assertRaises(TypeError, MContext.Cookie.from_cookie_header, cookie_av)

    def test_from_cookie_header_valid(self):
        cookie_av = b"foo={0}".format(MContext.Cookie.encode_value("bar"))
        instance = MContext.Cookie.from_cookie_header(cookie_av)
        self.assertEqual(instance.name, b"foo")
        self.assertEqual(instance.value, "bar")
        self.assertFalse(instance.httponly)
        self.assertFalse(instance.secure)
        self.assertIsNone(instance.expires)
        self.assertIsNone(instance.maxage)
        self.assertIsNone(instance.domain)
        self.assertIsNone(instance.path)
        self.assertTrue(instance.from_client)

    def test_from_cookie_header_invalid(self):
        cookie_av = b"foo"
        mocked_logging = Mocks.MockLogging(logging.getLogger())
        with mocked_logging:
            instance = MContext.Cookie.from_cookie_header(cookie_av)
            mocked_logging.assertLoggedCount("error", 1)
            self.assertIsNone(instance)

        cookie_av = b"foo;bar"
        with mocked_logging:
            instance = MContext.Cookie.from_cookie_header(cookie_av)
            mocked_logging.assertLoggedCount("error", 1)
            self.assertIsNone(instance)

    def test___init__(self):
        name = b"foo"
        value = "bar"
        instance = MContext.Cookie(name, value)
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.value, value)
        self.assertFalse(instance.httponly)
        self.assertFalse(instance.secure)
        self.assertIsNone(instance.expires)
        self.assertIsNone(instance.maxage)
        self.assertIsNone(instance.domain)
        self.assertIsNone(instance.path)
        self.assertFalse(instance.from_client)

    def test___init___warn_expires_and_maxage(self):
        # note that these are not actually valid parameters for both options,
        # but for this test it only matters that both are not None
        with Mocks.MockLogging(logging.getLogger()) as mocked_logging:
            instance = MContext.Cookie(b"foo", "bar", expires=True, maxage=True)
            mocked_logging.assertLoggedCount("warning", 1)

    def test_to_cookie_string_simple(self):
        name = b"foo"
        value = "bar"
        instance = MContext.Cookie(name, value)
        cookie_string = b"foo={0}".format(MContext.Cookie.encode_value(value))
        generated_cookie_string = instance.to_cookie_string()
        self.assertEqual(cookie_string, generated_cookie_string)
        self.assertIsInstance(generated_cookie_string, str)

    def test_to_cookie_string_with_attributes(self):
        name = b"foo"
        value = "bar"
        domain = "example.com"
        path = "/"
        instance = MContext.Cookie(name, value, domain=domain, path=path)
        cookie_string = b"foo={0}".format(MContext.Cookie.encode_value(value))
        cookie_string += "; Domain=" + domain + "; Path=" + path
        generated_cookie_string = instance.to_cookie_string()
        self.assertEqual(cookie_string, generated_cookie_string)
        self.assertIsInstance(generated_cookie_string, str)

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
