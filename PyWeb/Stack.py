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
        self.stale = False

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
        """
        Throw :cls:`PyWeb.Errors.HTTP.HTTP304` (Not Modified) if the value
        of *lastModified* is smaller than or equal to the current value of
        *ifModifiedSince* and *stale* is currently set to False.
        """
        if self.stale:
            return
        if self.ifModifiedSince is not None and lastModified is not None:
            if self.ifModifiedSince >= lastModified:
                raise Errors.NotModified()

    def overrideLastModified(self, timestamp):
        """
        Set *stale* to ``True`` if the given *timestamp* is newer than the
        current value of *ifModifiedSince*.

        This can be used to cancel any exceptions which would later be thrown
        by *checkNotModified*, for example when a dependency used to generate
        the output has changed.
        """
        if self.ifModifiedSince is not None:
            if timestamp > self.ifModifiedSince:
                self.ifModifiedSince = None

class WebStackSite(Site.Site):
    def __init__(self, sitemapFile, **kwargs):
        super(WebStackSite, self).__init__(sitemapFile, **kwargs)

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
