from __future__ import unicode_literals, print_function

import logging, itertools, collections, abc, functools, urllib, os, gc, urlparse

try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO

import PyXWF.utils as utils
import PyXWF.AcceptHeaders as AcceptHeaders
import PyXWF.Errors as Errors
import PyXWF.Context as Context
import PyXWF.Site as Site
import PyXWF.HTTPUtils as HTTPUtils

class WSGIContext(Context.Context):
    @classmethod
    def wsgiParseEnviron(self, environ):
        httpHeaders = {}
        httpIterator = itertools.ifilter(
            lambda x: x[0].startswith(b"HTTP_"),
            environ.iteritems())
        for key, value in httpIterator:
            header = key[5:].lower().replace(b"_", b"-")
            httpHeaders[header] = value

        hostName = httpHeaders.get("host", None) or environ.get("SERVER_NAME", None)
        try:
            serverPort = int(environ.get("SERVER_PORT"))
        except (ValueError, TypeError):
            serverPort = None
        relPath = environ.get("PATH_INFO").decode("utf-8")
        fullURI = environ.get("SCRIPT_NAME").decode("utf-8") + relPath
        urlScheme = environ.get("wsgi.scheme", "http")
        method = environ.get("REQUEST_METHOD")
        queryString = environ.get("QUERY_STRING", "")
        return (httpHeaders, method, urlScheme, hostName, serverPort,
                fullURI, relPath, queryString)

    def __init__(self, environ, start_response):
        super(WSGIContext, self).__init__()
        self._startResponse = start_response
        self._requestHeaders, \
        self._method, \
        self._scheme, \
        self._hostName, \
        self._serverPort, \
        self._fullURI, \
        self._path, \
        self._queryString, \
            = self.wsgiParseEnviron(environ)

        self._parseAcceptHeaders()
        self._parseNonAcceptHeaders()

        self._determineHTMLContentType()

    def _loadPreferenceList(self, headerName, prefList, default):
        try:
            headerValue = self._requestHeaders[headerName]
        except KeyError:
            headerValue = default
        prefList.appendHeader(headerValue)

    def _parseIfPresent(self, headerName, parseFunc, *args, **kwargs):
        try:
            headerValue = self._requestHeaders[headerName]
        except KeyError:
            return None
        else:
            return parseFunc(headerValue, *args, **kwargs)

    def _parseAcceptHeaders(self):
        self._accept = AcceptHeaders.AcceptPreferenceList()
        self._loadPreferenceList("accept", self._accept, "*/*")

        self._acceptCharset = AcceptHeaders.CharsetPreferenceList()
        self._loadPreferenceList("accept-charset", self._acceptCharset, "")
        self._acceptCharset.injectRFCValues()

        self._acceptLanguage = AcceptHeaders.LanguagePreferenceList()
        self._loadPreferenceList("accept-language", self._acceptLanguage, "*")

    def _parseNonAcceptHeaders(self):
        self._parseIfPresent("if-modified-since", self._parseIfModifiedSince)
        self._parseIfPresent("user-agent", self._parseUserAgent)

    def _parseIfModifiedSince(self, value):
        try:
            self._ifModifiedSince = HTTPUtils.parseHTTPDate(value)
        except Exception as err:
            raise Errors.BadRequest(message=str(err))

    def _parseUserAgent(self, value):
        self._userAgentName, \
        self._userAgentVersion \
            = utils.guessUserAgent(value)

        self._html5Support = self.userAgentSupportsHTML5(
            self._userAgentName,
            self._userAgentVersion
        )
        self._isMobileClient = utils.isMobileUserAgent(value)

    def _requireQuery(self):
        if self._queryData is None:
            self._queryData = urlparse.parse_qs(self._queryString)

    def sendResponse(self, message):
        body = self.getEncodedBody(message)
        if body is not None:
            self.setResponseContentType(message.MIMEType, message.Encoding)
        self._setCacheStatus()
        self._setPropertyHeaders()
        self._startResponse(
            b"{0:d} {1}".format(
                message.Status.code, message.Status.title
            ),
            self._responseHeaders.items()
        )
        if hasattr(body, "__iter__") and not isinstance(body, str):
            return iter(body)
        elif body is None:
            return []
        else:
            return utils.chunkString(body)


class WSGISite(Site.Site):
    def __init__(self, sitemapFile, **kwargs):
        super(WSGISite, self).__init__(sitemapFile, **kwargs)

    def getResponse(self, environ, start_response):
        try:
            try:
                ctx = WSGIContext(environ, start_response)
            except Errors.MalformedHTTPRequest as err:
                raise Errors.BadRequest(unicode(err))
            message = self.handle(ctx)
        except Errors.NotModified as status:
            return ctx.sendEmptyResponse(status)
        except Errors.HTTPRedirection as status:
            loc = status.location
            if status.local:
                if isinstance(loc, str):
                    loc = loc.decode("utf-8")
                if len(loc) > 0 and loc[0] == "/":
                    loc = loc[1:]
                loc = urllib.quote(os.path.join(self.urlRoot, loc).encode("utf-8"))
                loc = b"{0}://{1}{2}".format(
                    ctx.URLScheme,
                    ctx.HostName,
                    loc
                )
            ctx.setResponseHeader(b"Location", loc)
            return ctx.sendEmptyResponse(status)
        except (Errors.HTTPClientError, Errors.HTTPServerError) as status:
            ctx.Cachable = False
            if status.message is not None:
                message = Message.PlainTextMessage(contents=status.message,
                    status=status)
                return ctx.sendResponse(status)
            else:
                return ctx.sendEmptyResponse(status)
        else:
            return ctx.sendResponse(message)

    def __call__(self, environ, start_response):
        for item in self.getResponse(environ, start_response):
            yield item
        gc.collect()
