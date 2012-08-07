from __future__ import unicode_literals

import os, warnings, gc
from wsgiref.handlers import format_date_time
from datetime import datetime

import WebStack
from WebStack.Generic import EndOfResponse, ContentType

from PyWeb.utils import ET
import PyWeb.Errors as Errors
import PyWeb.Site as Site
import PyWeb.Context as Context
import PyWeb.HTTPUtils as HTTPUtils
import PyWeb.TimeUtils as TimeUtils

class WebStackContext(Context.Context):
    def __init__(self, transaction):
        super(WebStackContext, self).__init__(
            transaction.get_request_method(),
            transaction.get_path_info(),
            transaction.get_response_stream())
        self._transaction = transaction
        self._parseIfModifiedSince()

    @property
    def Out(self):
        return self._transaction.get_response_stream()

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

    def _requireQuery(self):
        raise NotImplemented()

    def _requirePost(self):
        raise NotImplemented()

    def _setCacheHeaders(self):
        tx = self._transaction
        if self.Cachable:
            lastModified = self.LastModified
            if lastModified is not None:
                tx.set_header_value("Last-Modified",
                    format_date_time(TimeUtils.toTimestamp(lastModified)))
            tx.set_header_value("Cache-Control", "must-revalidate")
        else:
            tx.set_header_value("Cache-Control", "no-cache")

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
            return
        except Errors.NotModified as status:
            transaction.set_response_code(status.statusCode)
            ctx._setCacheHeaders()
            return
        except Errors.HTTPRedirection as status:
            loc = status.newLocation
            if len(loc) > 0 and loc[0] == "/":
                loc = loc[1:]
            loc = os.path.join(self.urlRoot, loc)
            transaction.redirect(loc, status.statusCode)
            return
        except (Errors.HTTP200, EndOfResponse) as status:
            transaction.set_response_code(status.statusCode)
            return
        ctx.sendResponse(message)
        gc.collect()
