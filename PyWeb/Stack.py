import os

import WebStack
from WebStack.Generic import EndOfResponse

from PyWeb.utils import ET
import PyWeb.Errors as Errors
import PyWeb.Site as Site

class Context(object):
    def __init__(self, transaction):
        self.transaction = transaction
        self.method = transaction.get_request_method()
        self.path = transaction.get_path_info()
        self.out = transaction.get_response_stream()
        self.pageNode = None
        self.body = None

class WebStackSite(Site.Site):
    def __init__(self, sitemapFilelike=None, **kwargs):
        super(WebStackSite, self).__init__(sitemapFilelike)

    def respond(self, transaction):
        ctx = Context(transaction)
        try:
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
        message.getMessageInfo().applyToContext(ctx);
