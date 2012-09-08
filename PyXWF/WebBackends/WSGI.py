from __future__ import unicode_literals, print_function

import logging, itertools, collections, abc, functools, urllib, os, gc, urlparse

try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO

from PyXWF.utils import _F
import PyXWF.utils as utils
import PyXWF.AcceptHeaders as AcceptHeaders
import PyXWF.Errors as Errors
import PyXWF.Context as Context
import PyXWF.Site as Site
import PyXWF.HTTPUtils as HTTPUtils

class WSGIContext(Context.Context):
    @classmethod
    def wsgi_parse_environ(self, environ):
        http_headers = {}
        httpiter = itertools.ifilter(
            lambda x: x[0].startswith(b"HTTP_"),
            environ.iteritems())
        for key, value in httpiter:
            header = key[5:].lower().replace(b"_", b"-")
            http_headers[header] = value

        hostname = http_headers.get("host", None) or environ.get("SERVER_NAME", None)
        try:
            server_port = int(environ.get("SERVER_PORT"))
        except (ValueError, TypeError):
            server_port = None
        relpath = environ.get("PATH_INFO").decode("utf-8")
        url_scheme = environ.get("wsgi.scheme", "http")
        method = environ.get("REQUEST_METHOD")
        query_string = environ.get("QUERY_STRING", "")
        fulluri = environ.get("SCRIPT_NAME").decode("utf-8") + relpath + \
            (("?" + query_string) if query_string else "")
        return (http_headers, method, url_scheme, hostname, server_port,
                fulluri, relpath, query_string)

    def __init__(self, environ, start_response):
        super(WSGIContext, self).__init__()
        self._start_response = start_response
        self._request_headers, \
        self._method, \
        self._scheme, \
        self._hostname, \
        self._server_port, \
        self._fulluri, \
        self._path, \
        self._query_string, \
            = self.wsgi_parse_environ(environ)

        self._parse_accept_headers()
        self._parse_non_accept_headers()

        self._determine_html_content_type()

    def _load_preference_list(self, headername, preflist, default):
        try:
            headervalue = self._request_headers[headername]
        except KeyError:
            headervalue = default
        preflist.append_header(headervalue)

    def _parse_if_present(self, headername, parsefunc, *args, **kwargs):
        try:
            headervalue = self._request_headers[headername]
        except KeyError:
            return None
        else:
            return parsefunc(headervalue, *args, **kwargs)

    def _parse_accept_headers(self):
        self._accept = AcceptHeaders.AcceptPreferenceList()
        self._load_preference_list("accept", self._accept, "*/*")

        self._accept_charset = AcceptHeaders.CharsetPreferenceList()
        self._load_preference_list("accept-charset", self._accept_charset, "")
        self._accept_charset.inject_rfc_values()

        self._accept_language = AcceptHeaders.LanguagePreferenceList()
        self._load_preference_list("accept-language", self._accept_language, "*")

    def _parse_non_accept_headers(self):
        self._parse_if_present("if-modified-since", self._parse_if_modified_since)
        self._parse_if_present("user-agent", self._parse_user_agent)

    def _parse_if_modified_since(self, value):
        try:
            self._if_modified_since = HTTPUtils.parse_http_date(value)
        except Exception as err:
            raise Errors.BadRequest(message=str(err))

    def _parse_user_agent(self, value):
        self._useragent_name, \
        self._useragent_version \
            = utils.guess_useragent(value)

        self._html5_support = self.useragent_supports_html5(
            self._useragent_name,
            self._useragent_version
        )
        self._is_mobile_client = utils.is_mobile_useragent(value)

    def _require_query(self):
        if self._query_data is None:
            self._query_data = urlparse.parse_qs(self._query_string)

    def _require_post(self):
        raise NotImplementedError()

    def _require_cookies(self):
        cookie_value = self._request_headers.get("cookie", b"")
        self._cookies = self._parse_cookie_header(cookie_value)

    def send_response(self, message):
        body = self.get_encoded_body(message)
        if body is not None:
            self.set_response_content_type(message.MIMEType, message.Encoding)
        self._set_cache_status()
        self._set_property_headers()
        self._start_response(
            b"{0:d} {1}".format(
                message.Status.code, message.Status.title
            ),
            self._response_headers.items()
        )
        if hasattr(body, "__iter__") and not isinstance(body, str):
            return iter(body)
        elif body is None:
            return []
        else:
            return [body]


class WSGISite(Site.Site):
    def __init__(self, sitemap_file, **kwargs):
        super(WSGISite, self).__init__(sitemap_file, **kwargs)

    def get_response(self, environ, start_response):
        try:
            try:
                ctx = WSGIContext(environ, start_response)
            except Errors.MalformedHTTPRequest as err:
                raise Errors.BadRequest(unicode(err))
            message = self.handle(ctx)
        except Errors.NotModified as status:
            return ctx.send_empty_response(status)
        except Errors.HTTPRedirection as status:
            loc = status.location
            if status.local:
                if isinstance(loc, str):
                    loc = loc.decode("utf-8")
                if len(loc) > 0 and loc[0] == "/":
                    loc = loc[1:]
                loc = urllib.quote(os.path.join(self.urlroot, loc).encode("utf-8"))
                loc = b"{0}://{1}{2}".format(
                    ctx.URLScheme,
                    ctx.HostName,
                    loc
                )
            ctx.set_response_header(b"Location", loc)
            return ctx.send_empty_response(status)
        except (Errors.HTTPClientError, Errors.HTTPServerError) as status:
            ctx.Cachable = False
            if status.message is not None:
                message = Message.PlainTextMessage(contents=status.message,
                    status=status)
                return ctx.send_response(status)
            else:
                return ctx.send_empty_response(status)
        else:
            return ctx.send_response(message)

    def __call__(self, environ, start_response):
        for item in self.get_response(environ, start_response):
            yield item
        gc.collect()
