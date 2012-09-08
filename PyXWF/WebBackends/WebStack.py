from __future__ import unicode_literals, absolute_import

import os, warnings, gc, urllib
from datetime import datetime

import WebStack
from WebStack.Generic import EndOfResponse, ContentType

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Errors as Errors
import PyXWF.Site as Site
import PyXWF.Context as Context
import PyXWF.HTTPUtils as HTTPUtils
import PyXWF.TimeUtils as TimeUtils

class WebStackContext(Context.Context):
    def __init__(self, transaction):
        super(WebStackContext, self).__init__()
        self._method = transaction.get_request_method()
        self._path = transaction.get_path_info(encoding="utf-8")
        self._fulluri = transaction.get_path(encoding="utf-8")
        self._transaction = transaction
        self._parse_if_modified_since()
        self._parse_host_header()
        self._parse_environment()
        self._parse_preferences()
        self._parse_user_agent()
        self._determine_html_content_type()

    @property
    def Out(self):
        return self._transaction.get_response_stream()

    def _parse_if_modified_since(self):
        values = self._transaction.get_header_values("If-Modified-Since")
        if len(values) > 1:
            return
        if len(values) == 0:
            self._if_modified_since = None
            return
        try:
            self._if_modified_since = HTTPUtils.parse_http_date(values[0])
        except Exception as err:
            warnings.warn(err)

    def _parse_host_header(self):
        values = self._transaction.get_header_values("Host")
        if len(values) > 1:
            raise Errors.BadRequest(message="Too many host header fields.")
        if len(values) == 0:
            raise Errors.BadRequest(message="Sorry -- I need the Host header.")
        self._hostname = values[0]

    def _parse_environment(self):
        self._scheme = self._transaction.env["wsgi.url_scheme"]

    def _parse_preferences(self):
        tx = self._transaction

        self._accept = self.parse_accept(
            ",".join(tx.get_header_values("Accept"))
        )
        self._accept_charset = self.parse_accept_charset(
            ",".join(tx.get_header_values("Accept-Charset"))
        )

    def _parse_user_agent(self):
        tx = self._transaction
        values = self._transaction.get_header_values("User-Agent")
        if len(values) > 1:
            raise Errors.BadRequest(message="Too many User-Agent header fields.")
        if len(values) == 0:
            self._html5_support = False
            return

        header = values[0]
        useragent, version = utils.guess_useragent(header)
        self._useragent_name, self._useragent_version = useragent, version
        self._html5_support = self.useragent_supports_html5(useragent, version)
        self._is_mobile_client = utils.is_mobile_useragent(header)

    def _require_query(self):
        self._query_data = self._transaction.get_fields_from_path()

    def _require_post(self):
        raise NotImplemented()

    def _require_cookies(self):
        value = "; ".join(self._transaction.get_header_values("Cookie"))
        self._cookies = self._parse_cookie_header(value)

    def _headers_to_tx(self):
        tx = self._transaction
        for key, value in self._response_headers.viewitems():
            tx.set_header_value(key, value)

    def set_response_content_type(self, mimetype, charset):
        tx = self._transaction
        if charset:
            tx.set_content_type(ContentType(mimetype, charset))
        else:
            tx.set_content_type(ContentType(mimetype))

    def send_response(self, message):
        tx = self._transaction
        # this must be done before setting the content type, as the method also
        # determines the charset to use
        try:
            body = self.get_encoded_body(message)
        except Errors.NotAcceptable as err:
            tx.rollback()
            tx.set_response_code(message.StatusCode)
            return
        tx.rollback()
        tx.set_response_code(message.StatusCode)
        self.set_response_content_type(message.MIMEType, message.Encoding)
        self._set_cache_status()
        self._set_property_headers()
        self._headers_to_tx()
        self.Out.write(body)

class WebStackSite(Site.Site):
    def __init__(self, sitemap_file, **kwargs):
        super(WebStackSite, self).__init__(sitemap_file, **kwargs)

    def respond(self, transaction):
        try:
            try:
                ctx = WebStackContext(transaction)
            except Errors.MalformedHTTPRequest as err:
                raise Errors.BadRequest(unicode(err))
            message = self.handle(ctx)
        except (Errors.HTTPClientError, Errors.HTTPServerError) as status:
            transaction.set_response_code(status.code)
            ctx.Cachable = False
            ctx._set_cache_status()
            ctx._set_property_headers()
            ctx._headers_to_tx()
        except Errors.NotModified as status:
            transaction.set_response_code(status.code)
            ctx._set_cache_status()
            ctx._set_property_headers()
            ctx._headers_to_tx()
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
            ctx._set_cache_status()
            ctx._set_property_headers()
            ctx._headers_to_tx()
            transaction.redirect(loc, status.code)
        except (Errors.HTTPSuccessful, EndOfResponse) as status:
            transaction.set_response_code(status.code)
        else:
            ctx.send_response(message)
        transaction.commit()
        gc.collect()
