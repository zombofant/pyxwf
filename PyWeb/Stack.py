import os

import WebStack
from WebStack.Generic import EndOfResponse

from PyWeb.utils import ET
import PyWeb.Errors as Errors
import PyWeb.Site as Site

class WebStackSite(Site.Site):
    def __init__(self, sitemapFilelike=None, **kwargs):
        super(WebStackSite, self).__init__(sitemapFilelike)

    def respond(self, transaction):
        out = transaction.get_response_stream()
        transaction.path = transaction.get_path_info()
        transaction.method = transaction.get_request_method()
        try:
            message = self.handle(transaction, strip=False)
        except (Errors.HTTPClientError, Errors.HTTPServerError) as status:
            transaction.set_response_code(status.statusCode)
            return
        except Errors.NotModified as status:
            transaction.set_response_code(status.statusCode)
            return
        except Errors.HTTPRedirection as status:
            loc = os.path.join(self.urlRoot, status.newLocation)
            transaction.redirect(loc, status.statusCode)
            return
        except (Errors.HTTP200, EndOfResponse) as status:
            transaction.set_response_code(status.statusCode)
            return
        message.getMessageInfo().applyToTransaction(transaction);
