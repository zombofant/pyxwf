from __future__ import unicode_literals

import os, warnings, gc, urllib
from wsgiref.handlers import format_date_time
from datetime import datetime

import WebStack
from WebStack.Generic import EndOfResponse, ContentType

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Errors as Errors
import PyWeb.Site as Site
import PyWeb.Context as Context
import PyWeb.HTTPUtils as HTTPUtils
import PyWeb.TimeUtils as TimeUtils

class WebStackContext(Context.Context):
    def __init__(self, transaction):
        super(WebStackContext, self).__init__(
            transaction.get_request_method(),
            transaction.get_path_info(encoding="utf-8"),
            transaction.get_response_stream())
        self._fullURI = transaction.get_path(encoding="utf-8")
        self._transaction = transaction
        self._parseIfModifiedSince()
        self._parseHostHeader()
        self._parseEnvironment()
        self._parsePreferences()
        self._parseUserAgent()

    @property
    def Out(self):
        return self._transaction.get_response_stream()

    @property
    def HostName(self):
        return self._hostName

    @property
    def URLScheme(self):
        return self._scheme

    def _parseIfModifiedSince(self):
        values = self._transaction.get_header_values("If-Modified-Since")
        if len(values) > 1:
            return
        if len(values) == 0:
            self._ifModifiedSince = None
            return
        try:
            self._ifModifiedSince = HTTPUtils.parseHTTPDate(values[0])
        except Exception as err:
            warnings.warn(err)

    def _parseHostHeader(self):
        values = self._transaction.get_header_values("Host")
        if len(values) > 1:
            raise Errors.BadRequest(message="Too many host header fields.")
        if len(values) == 0:
            raise Errors.BadRequest(message="Sorry -- I need the Host header.")
        self._hostName = values[0]

    def _parseEnvironment(self):
        self._scheme = self._transaction.env["wsgi.url_scheme"]

    def _parsePreferences(self):
        tx = self._transaction

        self.parsePreferencesList(
            ",".join(tx.get_header_values("Accept"))
        )
        xhtmlContentType = self.getContentTypeToUse(
            ["application/xhtml+xml", "application/xml"],
            matchWildcard=False
        )

        self._canUseXHTML = xhtmlContentType is not None

    def _parseUserAgent(self):
        tx = self._transaction
        values = self._transaction.get_header_values("User-Agent")
        if len(values) > 1:
            raise Errors.BadRequest(message="Too many User-Agent header fields.")
        if len(values) == 0:
            self._html5Support = False
            return

        header = values[0]
        userAgent, version = utils.guessUserAgent(header)
        self._html5Support = self.userAgentSupportsHTML5(userAgent, version)

    def _requireQuery(self):
        self._queryData = self._transaction.get_fields_from_path()

    def _requirePost(self):
        raise NotImplemented()

    def _setCacheHeaders(self):
        tx = self._transaction
        if self.Cachable:
            lastModified = self.LastModified
            if lastModified is not None:
                self.addCacheControl("must-revalidate")
                tx.set_header_value("Last-Modified",
                    format_date_time(TimeUtils.toTimestamp(lastModified)))
        else:
            self.addCacheControl("no-cache")
        tx.set_header_value("Cache-Control", ",".join(self._cacheControl))
        tx.set_header_value("Vary", ",".join(self._vary))

    def sendResponse(self, message):
        tx = self._transaction
        tx.rollback()
        tx.set_response_code(message.StatusCode)
        tx.set_content_type(ContentType(message.MIMEType, message.Encoding))
        self._setCacheHeaders()
        self.Out.write(message.getEncodedBody())

class WebStackSite(Site.Site):
    def __init__(self, sitemapFile, **kwargs):
        super(WebStackSite, self).__init__(sitemapFile, **kwargs)

    def respond(self, transaction):
        try:
            try:
                ctx = WebStackContext(transaction)
            except Errors.MalformedHTTPRequset as err:
                raise Errors.BadRequest(unicode(err))
            message = self.handle(ctx)
        except (Errors.HTTPClientError, Errors.HTTPServerError) as status:
            transaction.set_response_code(status.statusCode)
        except Errors.NotModified as status:
            transaction.set_response_code(status.statusCode)
            ctx._setCacheHeaders()
        except Errors.HTTPRedirection as status:
            loc = status.newLocation
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
            ctx._setCacheHeaders()
            transaction.redirect(loc, status.statusCode)
        except (Errors.HTTP200, EndOfResponse) as status:
            transaction.set_response_code(status.statusCode)
        else:
            ctx.sendResponse(message)
        transaction.commit()
        gc.collect()
