from __future__ import unicode_literals, print_function

import unittest, wsgiref, wsgiref.util
from datetime import datetime

import PyXWF.Errors as Errors
import PyXWF.HTTPUtils as HTTPUtils
import PyXWF.TimeUtils as TimeUtils
import PyXWF.WebBackends.WSGI as WSGI

import tests.Mocks as Mocks

class WSGIContext(unittest.TestCase):
    def _start_response(self, status, headers, exc_info=None):
        self.assertIsNone(exc_info)
        self.assertIsNone(self.response_status)
        self.assertIsNone(self.response_headers)
        self.assertIsInstance(status, str)
        self.assertIsInstance(headers, list)
        for key, value in headers:
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
        headers.sort()
        self.response_headers = headers
        self.response_status = status

    def setup_environ(self, environ, custom_headers={}):
        wsgiref.util.setup_testing_defaults(environ)
        for header, value in custom_headers.items():
            key = b"HTTP_"+str(header).replace(b"-", b"_").upper()
            environ[key] = str(value)

    def setup_querystring_environ(self, environ, root="/", local="", query="", **kwargs):
        self.setup_environ(environ, **kwargs)
        environ["QUERY_STRING"] = query
        environ["SCRIPT_NAME"] = root
        environ["PATH_INFO"] = local

    def send_message(self, body="Foo bar", **kwargs):
        ctx = self.get_context(**kwargs)
        message = Message.TextMessage(body, encoding="utf-8")
        self.response_body = "".join(ctx.send_response(message))
        return ctx

    def setUp(self):
        self.response_headers = None
        self.response_status = None

    def get_context(self, *args, **kwargs):
        if len(args) == 0:
            envsetup = self.setup_environ
        else:
            args = list(args)
            envsetup = args.pop(0)
        environ = {}
        envsetup(environ, *args, **kwargs)
        return WSGI.WSGIContext(environ, self._start_response)

    def tearDown(self):
        del self.response_headers
        del self.response_status

    def test_header_parsing(self):
        myheaders = {
            "user-agent": "unknown",
        }
        ctx = self.get_context(custom_headers=myheaders)
        myheaders.update({"host": ctx.HostName})
        self.assertEqual(ctx._request_headers, myheaders)

    def test_uri_properties(self):
        ctx = self.get_context(self.setup_querystring_environ, local="foo/bar", query="quux=baz")
        self.assertEqual(ctx.FullURI, "/foo/bar?quux=baz")
        self.assertEqual(ctx.Path, "foo/bar")
        self.assertEqual(ctx.QueryData, {"quux": ["baz"]})

    def test_if_modified_since_bad_request(self):
        self.assertRaises(Errors.BadRequest, self.get_context, custom_headers={
            "if-modified-since": "foobar"
        })

    def test_if_modified_since_rfc_822_and_1123(self):
        ctx = self.get_context(custom_headers={
            "If-Modified-Since": "Sun, 06 Nov 1994 08:49:37 GMT"
        })
        self.assertEqual(ctx.IfModifiedSince, datetime(
            1994, 11, 6,
            8, 49, 37
        ))

    def test_if_modified_since_rfc_850_1036(self):
        ctx = self.get_context(custom_headers={
            "If-Modified-Since": "Sunday, 06-Nov-94 08:49:37 GMT"
        })
        self.assertEqual(ctx.IfModifiedSince, datetime(
            1994, 11, 6,
            8, 49, 37
        ))

    def test_if_modified_since_asctime(self):
        ctx = self.get_context(custom_headers={
            "If-Modified-Since": "Sun Nov  6 08:49:37 1994"
        })
        self.assertEqual(ctx.IfModifiedSince, datetime(
            1994, 11, 6,
            8, 49, 37
        ))

    def test_xhtml_vs_html(self):
        ctx = self.get_context(custom_headers={
            "Accept": "application/xhtml+xml;q=0.9, text/html"
        })
        self.assertFalse(ctx.CanUseXHTML)

        ctx = self.get_context(custom_headers={
            "Accept": "application/xhtml+xml;q=1.0, text/html"
        })
        self.assertTrue(ctx.CanUseXHTML)

        ctx = self.get_context(custom_headers={
            "Accept": "*/*;q=1.0, text/html"
        })
        self.assertFalse(ctx.CanUseXHTML)

        ctx = self.get_context(custom_headers={
            "Accept": "text/plain, application/xhtml+xml;q=0.8, text/html;q=0.8"
        })
        self.assertTrue(ctx.CanUseXHTML)

        ctx = self.get_context(custom_headers={
            "Accept": "text/plain, application/xhtml+xml;q=0.8, text/html;q=0.8"
        })
        self.assertTrue(ctx.CanUseXHTML)

    def test_acceptable(self):
        ctx = self.get_context(custom_headers={
            "Accept": "text/html;level=1"
        })
        self.assertRaises(Errors.NotAcceptable, ctx.check_acceptable, "text/html")

        ctx = self.get_context(custom_headers={
            "Accept": "text/html;q=0.9, text/html;level=1"
        })
        ctx.check_acceptable("text/html")

    def test_empty_response(self):
        ctx = self.get_context(custom_headers={
            "Accept": "text/html;level=1"
        })
        ctx.send_empty_response(Errors.OK)
        self.assertEqual(self.response_status, "200 OK")
        self.assertEqual(self.response_headers, [
            (b"vary", b"host")
        ])

    def test_response_headers(self):
        ctx = self.get_context()
        ctx.set_response_header("X-Foo", "BaR")
        ctx.send_empty_response(Errors.OK)
        self.assertEqual(self.response_headers, [
            (b"vary", b"host"),
            (b"x-foo", b"BaR")
        ])

    def test_no_cache(self):
        ctx = self.get_context()
        ctx.Cachable = False
        ctx.send_empty_response(Errors.OK)
        self.assertEqual(self.response_headers, [
            (b"cache-control", b"no-cache"),
            (b"vary", b"host")
        ])

    def test_last_modified(self):
        res = Mocks.FakeResource()
        d = datetime.utcnow()
        res.LastModified = d
        ctx = self.get_context()
        ctx.use_resource(res)
        ctx.send_empty_response(Errors.OK)
        self.assertEqual(self.response_headers, [
            (b"cache-control", b"must-revalidate"),
            (b"last-modified", HTTPUtils.format_http_date(d)),
            (b"vary", b"host")
        ])

    def test_not_modified(self):
        res = Mocks.FakeResource()
        d = TimeUtils.strip_microseconds(datetime.utcnow())
        res.LastModified = d
        ctx = self.get_context(custom_headers={
            b"if-modified-since": HTTPUtils.format_http_date(d)
        })
        ctx.use_resource(res)
        self.assertEqual(ctx.LastModified, d)
        self.assertEqual(ctx.IfModifiedSince, d)
        self.assertRaises(Errors.NotModified, ctx.check_not_modified)
        ctx.send_empty_response(Errors.OK)
        self.assertEqual(self.response_headers, [
            (b"cache-control", b"must-revalidate"),
            (b"last-modified", HTTPUtils.format_http_date(d)),
            (b"vary", b"host,if-modified-since")
        ])
