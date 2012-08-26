from __future__ import unicode_literals, print_function

import unittest, wsgiref, wsgiref.util
from datetime import datetime

import PyXWF.Errors as Errors
import PyXWF.HTTPUtils as HTTPUtils
import PyXWF.TimeUtils as TimeUtils
import PyXWF.WebBackends.WSGI as WSGI

import tests.Mocks as Mocks

class WSGIContext(unittest.TestCase):
    def _startResponse(self, status, headers, exc_info=None):
        self.assertIsNone(exc_info)
        self.assertIsNone(self.responseStatus)
        self.assertIsNone(self.responseHeaders)
        self.assertIsInstance(status, str)
        self.assertIsInstance(headers, list)
        for key, value in headers:
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
        headers.sort()
        self.responseHeaders = headers
        self.responseStatus = status

    def setUpEnviron(self, environ, customHeaders={}):
        wsgiref.util.setup_testing_defaults(environ)
        for header, value in customHeaders.items():
            key = b"HTTP_"+str(header).replace(b"-", b"_").upper()
            environ[key] = str(value)

    def sendMessage(self, body="Foo bar", **kwargs):
        ctx = self.getContext(**kwargs)
        message = Message.TextMessage(body, encoding="utf-8")
        self.responseBody = "".join(ctx.sendResponse(message))
        return ctx

    def setUp(self):
        self.responseHeaders = None
        self.responseStatus = None

    def getContext(self, *args, **kwargs):
        if len(args) == 0:
            envSetup = self.setUpEnviron
        else:
            args = list(args)
            envSetup = args.pop(0)
        environ = {}
        envSetup(environ, *args, **kwargs)
        return WSGI.WSGIContext(environ, self._startResponse)

    def tearDown(self):
        del self.responseHeaders
        del self.responseStatus

    def test_headerParsing(self):
        myHeaders = {
            "user-agent": "unknown",
        }
        ctx = self.getContext(customHeaders=myHeaders)
        myHeaders.update({"host": ctx.HostName})
        self.assertEqual(ctx._requestHeaders, myHeaders)

    def test_ifModifiedSince_BadRequest(self):
        self.assertRaises(Errors.BadRequest, self.getContext, customHeaders={
            "if-modified-since": "foobar"
        })

    def test_ifModifiedSince_RFC822_1123(self):
        ctx = self.getContext(customHeaders={
            "If-Modified-Since": "Sun, 06 Nov 1994 08:49:37 GMT"
        })
        self.assertEqual(ctx.IfModifiedSince, datetime(
            1994, 11, 6,
            8, 49, 37
        ))

    def test_ifModifiedSince_RFC850_1036(self):
        ctx = self.getContext(customHeaders={
            "If-Modified-Since": "Sunday, 06-Nov-94 08:49:37 GMT"
        })
        self.assertEqual(ctx.IfModifiedSince, datetime(
            1994, 11, 6,
            8, 49, 37
        ))

    def test_ifModifiedSince_asctime(self):
        ctx = self.getContext(customHeaders={
            "If-Modified-Since": "Sun Nov  6 08:49:37 1994"
        })
        self.assertEqual(ctx.IfModifiedSince, datetime(
            1994, 11, 6,
            8, 49, 37
        ))

    def test_xhtml_vs_html(self):
        ctx = self.getContext(customHeaders={
            "Accept": "application/xhtml+xml;q=0.9, text/html"
        })
        self.assertFalse(ctx.CanUseXHTML)

        ctx = self.getContext(customHeaders={
            "Accept": "application/xhtml+xml;q=1.0, text/html"
        })
        self.assertTrue(ctx.CanUseXHTML)

        ctx = self.getContext(customHeaders={
            "Accept": "*/*;q=1.0, text/html"
        })
        self.assertFalse(ctx.CanUseXHTML)

        ctx = self.getContext(customHeaders={
            "Accept": "text/plain, application/xhtml+xml;q=0.8, text/html;q=0.8"
        })
        self.assertTrue(ctx.CanUseXHTML)

        ctx = self.getContext(customHeaders={
            "Accept": "text/plain, application/xhtml+xml;q=0.8, text/html;q=0.8"
        })
        self.assertTrue(ctx.CanUseXHTML)

    def test_acceptable(self):
        ctx = self.getContext(customHeaders={
            "Accept": "text/html;level=1"
        })
        self.assertRaises(Errors.NotAcceptable, ctx.checkAcceptable, "text/html")

        ctx = self.getContext(customHeaders={
            "Accept": "text/html;q=0.9, text/html;level=1"
        })
        ctx.checkAcceptable("text/html")

    def test_emptyResponse(self):
        ctx = self.getContext(customHeaders={
            "Accept": "text/html;level=1"
        })
        ctx.sendEmptyResponse(Errors.OK)
        self.assertEqual(self.responseStatus, "200 OK")
        self.assertEqual(self.responseHeaders, [
            (b"vary", b"host")
        ])

    def test_responseHeaders(self):
        ctx = self.getContext()
        ctx.setResponseHeader("X-Foo", "BaR")
        ctx.sendEmptyResponse(Errors.OK)
        self.assertEqual(self.responseHeaders, [
            (b"vary", b"host"),
            (b"x-foo", b"BaR")
        ])

    def test_noCache(self):
        ctx = self.getContext()
        ctx.Cachable = False
        ctx.sendEmptyResponse(Errors.OK)
        self.assertEqual(self.responseHeaders, [
            (b"cache-control", b"no-cache"),
            (b"vary", b"host")
        ])

    def test_lastModified(self):
        res = Mocks.FakeResource()
        d = datetime.utcnow()
        res.LastModified = d
        ctx = self.getContext()
        ctx.useResource(res)
        ctx.sendEmptyResponse(Errors.OK)
        self.assertEqual(self.responseHeaders, [
            (b"cache-control", b"must-revalidate"),
            (b"last-modified", HTTPUtils.formatHTTPDate(d)),
            (b"vary", b"host")
        ])

    def test_notModified(self):
        res = Mocks.FakeResource()
        d = TimeUtils.stripMicroseconds(datetime.utcnow())
        res.LastModified = d
        ctx = self.getContext(customHeaders={
            b"if-modified-since": HTTPUtils.formatHTTPDate(d)
        })
        ctx.useResource(res)
        self.assertEqual(ctx.LastModified, d)
        self.assertEqual(ctx.IfModifiedSince, d)
        self.assertRaises(Errors.NotModified, ctx.checkNotModified)
        ctx.sendEmptyResponse(Errors.OK)
        self.assertEqual(self.responseHeaders, [
            (b"cache-control", b"must-revalidate"),
            (b"last-modified", HTTPUtils.formatHTTPDate(d)),
            (b"vary", b"host,if-modified-since")
        ])
