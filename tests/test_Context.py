# encoding=utf-8
from __future__ import unicode_literals

import unittest

import PyXWF.Context as MContext
import PyXWF.Message as Message
import PyXWF.Errors as Errors

import tests.Mocks as Mocks

class Preference(unittest.TestCase):
    def test_ordering(self):
        P = MContext.Preference
        # from https://tools.ietf.org/html/rfc2616#section-14.1
        # (HTTP/1.1, section 14.1)

        p1 = P("text/*", 1.0)
        p2 = P("text/html", 1.0)
        p3 = P("text/html", 1.0, parameters={"level": "1"})
        p4 = P("*/*", 1.0)

        correctOrdering = [p3, p2, p1, p4]
        inputOrdering = [p1, p2, p3, p4]
        inputOrdering.sort(reverse=True)

        self.assertSequenceEqual(correctOrdering, inputOrdering)

    def test_ordering2(self):
        P = MContext.Preference
        # from https://tools.ietf.org/html/rfc2616#section-14.1
        # (HTTP/1.1, section 14.1)

        p1 = P("audio/*", 0.2)
        p2 = P("audio/basic", 1.0)

        correctOrdering = [p2, p1]
        inputOrdering = [p1, p2]
        inputOrdering.sort(reverse=True)

        self.assertSequenceEqual(correctOrdering, inputOrdering)

    def test_parsing(self):
        P = MContext.Preference
        header = """text/plain; q=0.5, text/html,
                    text/x-dvi; q=0.8, text/x-c"""
        self.assertSequenceEqual(P.listFromHeader(header),
            [
                P("text/html", 1.0),
                P("text/x-c", 1.0),
                P("text/x-dvi", 0.8),
                P("text/plain", 0.5)
            ]
        )

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

    def test_charsetISOInclusion(self):
        ctx = self.sendMessage(body="äöü", acceptCharset="ascii")
        self.assertEqual(ctx.Out.getvalue(), b"""\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=iso-8859-1

"""+"""äöü""".encode("iso-8859-1"))

    def test_charsetNoFallback(self):
        self.assertRaises(Errors.NotAcceptable, self.sendMessage, body="äöü", acceptCharset="ascii,*;q=0")

    def test_charsetDetection_complex(self):
        ctx = self.sendMessage(body="😸", acceptCharset="ascii,latin-1;q=0.9,utf-32be;q=0.8,utf-32le;q=0.8,utf-8;q=0.7,*;q=0")
        self.assertEqual(ctx.Out.getvalue(), b"""\
200 Mocked Status Code
vary: host
content-type: text/plain; charset=utf-32le

"""+"""😸""".encode("utf-32le"))

    def test_HTTP_1_1_section_14_1(self):
        ctx = Mocks.MockedContext("")
        prefs = ctx.parseAccept("""text/*;q=0.3, text/html;q=0.7, text/html;level=1,
               text/html;level=2;q=0.4, */*;q=0.5""")

        P = MContext.Preference
        expectedPrecedence = [
            (P.fromHeaderSection("text/html;level=1"),     1),
            (P.fromHeaderSection("text/html"),             0.7),
            (P.fromHeaderSection("text/plain"),            0.3),
            (P.fromHeaderSection("image/jpeg"),            0.5),
            (P.fromHeaderSection("text/html;level=2"),     0.4),
            (P.fromHeaderSection("text/html;level=3"),     0.7),
        ]

        for pref, q in expectedPrecedence:
            candidates = ctx.getPreferenceCandidates(prefs, [pref])
            precedence = candidates.pop()[0]
            self.assertEqual(q, precedence, msg="{0} did not get the correct q-value: {1} expected, {2} calculated".format(
                pref,
                q,
                precedence
            ))
