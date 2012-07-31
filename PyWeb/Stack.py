from __future__ import unicode_literals

import os

import WebStack
from WebStack.Generic import EndOfResponse

from PyWeb.utils import ET
import PyWeb.Errors as Errors
import PyWeb.Site as Site
import PyWeb.HTTPUtils as HTTPUtils

class Context(object):
    def __init__(self, transaction):
        self.transaction = transaction
        self.method = transaction.get_request_method()
        self.path = transaction.get_path_info()
        self.out = transaction.get_response_stream()
        self.pageNode = None
        self.body = None
        self.ifModifiedSince = None

        self._parseIfModifiedSince()

    def _parseIfModifiedSince(self):
        values = self.transaction.get_header_values("If-Modified-Since")
        if len(values) > 1:
            raise Errors.MalformedHTTPRequset("If-Modified-Since is present multiple times.")
        if len(values) == 0:
            self.ifModifiedSince = None
            return
        self.ifModifiedSince = HTTPUtils.parseHTTPDate(values[0])

    def checkNotModified(self, lastModified):
        if self.ifModifiedSince is not None and lastModified is not None:
            if self.ifModifiedSince >= lastModified:
                raise Errors.NotModified()

class WebStackSite(Site.Site):
    def __init__(self, sitemapFilelike=None, **kwargs):
        super(WebStackSite, self).__init__(sitemapFilelike)

    def respond(self, transaction):
        try:
            try:
                ctx = Context(transaction)
            except Errors.MalformedHTTPRequset as err:
                raise Errors.BadRequest(unicode(err))
            message = self.handle(ctx, strip=False)
        except (Errors.HTTPClientError, Errors.HTTPServerError) as status:
            transaction.set_response_code(status.statusCode)
            return
        except Errors.NotModified as status:
            transaction.set_response_code(status.statusCode)
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
        message.sendInContext(ctx);
