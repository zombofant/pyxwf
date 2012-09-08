# encoding=utf-8
from __future__ import unicode_literals, print_function

import operator
import abc
import collections
import functools
import logging
import itertools
import base64

from PyXWF.utils import _F
import PyXWF.Types as Types
import PyXWF.Errors as Errors
import PyXWF.TimeUtils as TimeUtils
import PyXWF.ContentTypes as ContentTypes
import PyXWF.HTTPUtils as HTTPUtils
import PyXWF.AcceptHeaders as AcceptHeaders
import PyXWF.Message as Message

logging = logging.getLogger(__name__)

class Cookie(object):
    @staticmethod
    def decode_value(value):
        missing = 4 - len(value) % 4
        if 0 < missing < 4:
            value += b"=" * missing
        return base64.urlsafe_b64decode(value).decode(b"utf-8")

    @staticmethod
    def encode_value(value):
        if isinstance(value, unicode):
            value = value.encode(b"utf-8")
        encoded = base64.urlsafe_b64encode(value)
        return encoded.rstrip(b"=")

    @classmethod
    def from_cookie_header(cls, cookie_pair):
        """
        Return the :class:`~Cookie` instance by parsing *cookie_pair* as per
        RFC 6265, Section 4.2.1.

        If the decoding of *cookie_pair* fails for some reason, None is returned
        and an error is logged.
        """
        if not isinstance(cookie_pair, str):
            raise TypeError("cookie_pair must be str, not {0}".format(type(cookie_pair).__name__))
        try:
            if b";" in cookie_pair:
                raise ValueError("cookie_pair contains \";\"")
            name, _, value = cookie_pair.partition(b"=")
            if not value:
                raise ValueError("cookie_pair does not conform to RFC 6265 (no value)")
            instance = cls(name, cls.decode_value(value))
        except (ValueError, TypeError) as err:
            logging.error(_F(
                "Could not decode cookie-av {0!r}: {1}",
                cookie_pair,
                err
            ))
            return None
        instance.from_client = True
        return instance

    def __init__(self, name, value,
            expires=None, domain=None, path=None, secure=False, httponly=False,
            maxage=None):
        if expires is not None and maxage is not None:
            logging.warning("Cookie has both maxage and expires, maxage will \
take precedence")
        self.name = str(name)
        self.value = value
        self.expires = expires
        self.domain = str(domain) if domain is not None else None
        self.path = str(path) if path is not None else None
        self.secure = bool(secure)
        self.httponly = bool(httponly)
        self.maxage = int(maxage) if maxage is not None else None
        self.from_client = False

    def to_cookie_string(self):
        cookie_pair = b"{0}={1}".format(self.name, self.encode_value(self.value))
        cookie_avs = []
        if self.domain:
            cookie_avs.append(b"Domain={0}".format(self.domain))
        if self.path is not None:
            cookie_avs.append(b"Path={0}".format(self.path))
        if self.expires is not None:
            cookie_avs.append(b"Expires={0}".format(
                HTTPUtils.format_http_date(self.expires)
            ))
        if self.maxage is not None:
            cookie_avs.append(b"Max-Age={0:d}".format(self.maxage))
        if self.secure:
            cookie_avs.append(b"Secure")
        if self.httponly:
            cookie_avs.append(b"HttpOnly")
        if cookie_avs:
            cookie_avs.insert(0, b"")
        return cookie_pair + b"; ".join(cookie_avs)

    def __eq__(self, other):
        try:
            return (
                self.name == other.name and
                self.value == other.value and
                self.expires == other.expires and
                self.domain == other.domain and
                self.path == other.path and
                self.secure == other.secure and
                self.httponly == other.httponly and
                self.maxage == other.maxage
            )
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        result = self == other
        if result is not NotImplemented:
            return not result
        return result

    def __repr__(self):
        return "<Cookie {0}={1!r} domain={2!r} path={3!r} expires={4} maxage={5}{6}>".format(
            self.name,
            self.value,
            self.domain,
            self.path,
            self.expires,
            self.maxage,
            " ".join(attr for attr in [
                "secure" if self.secure else None,
                "httponly" if self.httponly else None
            ] if attr is not None)
        )


class Context(object):
    """
    The context of a request. It is passed around when retrieving the Document
    from the Node tree and can be used to store custom data. All the properties
    of the framework are named with a capital first letter or prefixed with an
    underscore, so you're safe to use all other names.

    .. note::
        Do not instanciate this class directly. The web backend will do it for
        you.

    If you are going to write a web backend, we suggest you have a look at
    the :mod:`PyXWF.WebBackends.WSGI` module as a reference. There is a
    whole bunch of internal attributes which need to be set up to get the
    Context work properly.
    """
    __metaclass__ = abc.ABCMeta

    html_preferences = [
        # prefer delivery of XHTML (no conversion required)
        AcceptHeaders.AcceptPreference("application/xhtml+xml", 1.0),
        AcceptHeaders.AcceptPreference("text/html", 0.9)
    ]

    charset_preferences = [
        # prefer UTF-8, then go through the other unicode encodings in
        # ascending order of size. prefer little-endian over big-endian
        # encodings
        AcceptHeaders.CharsetPreference("utf-8", 1.0),
        AcceptHeaders.CharsetPreference("utf-16le", 0.95),
        AcceptHeaders.CharsetPreference("utf-16be", 0.9),
        AcceptHeaders.CharsetPreference("ucs-2le", 0.85),
        AcceptHeaders.CharsetPreference("ucs-2be", 0.8),
        AcceptHeaders.CharsetPreference("utf-32le", 0.75),
        AcceptHeaders.CharsetPreference("utf-32be", 0.7),
    ]

    useragent_html5_support = {
        "ie": 9.0,
        "firefox": 4.0,
        "chrome": 6.0,
        "safari": 5.0,
        "opera": 11.1
    }

    def __init__(self):
        # Method of the HTTP request ("GET", "POST", ...)
        self._method = None

        # path relative to the application's root
        self._path = None

        # query data, as a python dict (can be initialized lazily in
        # :meth:`_require_query` )
        self._query_data = None

        # query data, as a python dict (can be initialized lazily in
        # :meth:`_require_post` )
        self._post_data = None

        # cookie information, as a python dict (can be initialized lazily in
        # :meth:`_require_cookies` )
        self._cookies = None

        # datetime object representing the value of the incoming
        # If-Modified-Since header, if any. Otherwise None
        self._if_modified_since = None

        # :class:`AcceptPreferenceList` instance
        self._accept = None

        # :class:`CharsetPreferenceList` instance
        self._accept_charset = None

        # :class:`LanguagePreferenceList` instance
        self._accept_language = None

        # will be set to True if POST data was requested (can be avoided by not
        # calling super()._require_post when overriding _require_post)
        self._force_no_cache = False

        # these are backing values for the properties below. See their
        # docstrings for further information
        self._cachable = True
        self._pagenode = None
        self._used_resources = set()
        self._last_modified = None
        self._can_use_xhtml = False
        self._cache_control = set()
        self._html5_support = False
        self._useragent_name = None
        self._useragent_version = None
        self._is_mobile_client = False
        self._response_headers = {}
        self._vary = set(["host"])

    @abc.abstractmethod
    def _require_query(self):
        """
        Extract query string from the web frameworks transaction and make it
        accessible. Also make a note that the query string was used in this
        request and is thus needs to be appended to the cache path.

        .. note::
            This must be overridden when implementing a Context for a specific
            web backend.
        """

    @abc.abstractmethod
    def _require_post(self):
        """
        Extract the post data from the request and make it available at
        :attr:`PostData`. This disables caching of the response altogether.

        .. note::
            This must be overridden when implementing a Context for a specific
            web backend.
        """
        self._force_no_cache = True

    @abc.abstractmethod
    def _require_cookies(self):
        """
        Extract the cookie information from the request and make it available at
        :attr:`Cookies`.

        .. note::
            This must be overriden when implementing a Context for a specific
            web backend. It is expected that this method sets the
            :attr:`_cookies` attribute to a dict mapping cookie names to
            :class:`~Cookie` instances.
        """

    def _set_cache_status(self):
        """
        Use the values of :attr:`Cachable` and :attr:`LastModified` to set up
        the response headers which relate to caching. This may change the value
        of the ``Last-Modified`` header and will add a cache control token.
        """
        if self.Cachable:
            last_modified = self.LastModified
            if last_modified is not None:
                self.add_cache_control("must-revalidate")
                self.set_response_header("Last-Modified",
                    HTTPUtils.format_http_date(last_modified))
        else:
            self.add_cache_control("no-cache")

    def _determine_html_content_type(self):
        """
        Use the :class:`~PyXWF.AcceptHeaders.AcceptPreferenceList` instance to
        figure out whether the client properly supports XHTML.

        Will set :attr:`~.CanUseXHTML` to True if the best match for all HTML
        content types is the XHTML content type.
        """
        logging.debug(_F("Finding out HTML content type to use. User agent: {0}/{1:.2f}",
            self._useragent_name, self._useragent_version))
        if self._useragent_name == "ie" and self._useragent_version < 9:
            # thank you, microsoft, for your really verbose accept headers -
            # which do _not_ include an explicit mention of text/html, instead,
            # you just assume you can q=1.0 everything.
            logging.debug("Forcing XHTML support to false: MSIE < 9 detected!")
            html_content_type = ContentTypes.html
        elif self._useragent_name == "chrome" and self._useragent_version < 7:
            # but open browsers are not neccessarily better -- chromium with
            # version <= 6.0 sends:
            # application/xml;q=1.00, application/xhtml+xml;q=1.00, \
            # text/html;q=0.90, text/plain;q=0.80, image/png;q=1.00, */*;q=0.50
            # but is in fact unable to parse valid XHTML.
            logging.debug("Forcing XHTML support to false: Chrome < 7 detected!")
            html_content_type = ContentTypes.html
        else:
            logging.debug("Accept: {0}".format(", ".join(map(str, self._accept))))
            html_content_type = self._accept.best_match(
                self.html_preferences,
                match_wildcard=False
            )
        self._can_use_xhtml = html_content_type == ContentTypes.xhtml
        logging.debug("CanUseXHTML: {0}".format(self._can_use_xhtml))
        return html_content_type

    def _set_property_headers(self):
        """
        Convert :attr:`~.Vary` and :attr:`~.CacheControl` into HTTP headers and
        add them to the response headers.
        """
        if self._vary:
            self.set_response_header(b"vary", b",".join(self._vary))
        else:
            self.clear_response_header(b"vary")

        if self._cache_control:
            self.set_response_header(b"cache-control", b",".join(self._cache_control))
        else:
            self.clear_response_header(b"cache-control")

    def parse_accept(self, header_value):
        """
        Parse *header_value* as value of an HTTP ``Accept`` header and return the
        resulting :class:`~PyXWF.AcceptHeaders.AcceptPreferenceList` instance.
        """
        prefs = AcceptHeaders.AcceptPreferenceList()
        prefs.append_header(header_value)
        return prefs

    def parse_accept_charset(self, header_value):
        """
        Parse *header_value* as value of an HTTP ``Accept-Charset`` header and
        return the resulting :class:`~PyXWF.AcceptHeaders.CharsetPreferenceList`
        instance.
        """
        prefs = AcceptHeaders.CharsetPreferenceList()
        prefs.append_header(header_value)
        prefs.inject_rfc_values()
        return prefs

    def get_encoded_body(self, message):
        """
        Try to get the best encoded version of the
        :class:`~PyXWF.Message.Message` instance *message*.

        Use the contents of :attr:`_accept_charset` (the parsed
        ``Accept-Charset`` HTTP header) to figure out which charsets the client
        prefers. Then mix in what charsets _we_ like to deliver and get the
        best match, giving priority to the clients wishes.

        If no matching encoding can be found,
        :class:`~PyXWF.Errors.NotAcceptable` is raised.
        """
        candidates = self._accept_charset.get_candidates(
            self.charset_preferences,
            match_wildcard=True,
            include_non_matching=True,
            take_everything_on_empty=True)

        # to prevent denial of service, we only test the first five encodings
        for q, encoding in itertools.islice(reversed(candidates), 0, 5):
            try:
                message.Encoding = encoding
                return message.get_encoded_body()
            except UnicodeEncodeError:
                pass
        else:
            # we try to serve the client UTF-8 and log a warning
            logging.warning("No charset the client presented us worked to encode the message, returning 406 Not Acceptable")
            logging.debug("Accept-Charset: {0}".format(", ".join(map(str, self._accept_charset))))
            raise Errors.NotAcceptable()

    @classmethod
    def useragent_supports_html5(cls, useragent, version):
        """
        Guess whether the user agent *useragent* with version *version* (as
        obtained for example from :func:`PyXWF.utils.guess_useragent`) can deal
        with HTML5. This is only more or less accurate for the popular browsers.
        Everyone else will just be served HTML5.
        """
        try:
            minversion = cls.useragent_html5_support[useragent]
            return version >= minversion
        except KeyError:
            return True  # we assume the best ... let them burn

    @classmethod
    def _parse_cookie_header(cls, value):
        cookie_strings = value.split(b";")
        parse_cookie_gen = (Cookie.from_cookie_header(cookie_string.lstrip()) for cookie_string in cookie_strings)
        cookies = (cookie for cookie in parse_cookie_gen if cookie is not None)
        return dict((cookie.name, cookie) for cookie in cookies)

    @property
    def Method(self):
        """
        The request method (i.e. GET, POST
        , HEAD, ...)
        """
        return self._method

    @property
    def RequestPath(self):
        """
        The URL path for the request, relative to the applications (not the
        servers) root.
        """
        return self._path

    @property
    def FullURI(self):
        """
        The URL path for the request. This is everything behind the host name
        and the port number.
        """
        return self._fulluri

    @property
    def HostName(self):
        """
        Host name the request was sent to.
        """
        return self._hostname

    @property
    def URLScheme(self):
        """
        URL scheme used for the request (this is either ``http`` or ``https``).
        """
        return self._scheme

    Path = RequestPath

    @property
    def QueryData(self):
        """
        Access to the GET query data of the request as a dict. Accessing this
        property will add the query string to the cache path.
        """
        self._require_query()
        return self._query_data

    @property
    def PostData(self):
        """
        Access to the POST data of the request. Accessing this property will
        disable caching of the response.
        """
        self._require_post()
        return self._post_data

    @property
    def RemainingPath(self):
        """
        Path suffix which was not interpreted during resolution of the path
        inside the node tree. This may be useful for redirects.
        """
        return self._rempath

    @RemainingPath.setter
    def RemainingPath(self, value):
        self._rempath = Typecasts.Types.unicode(value)

    @property
    def Cachable(self):
        """
        Set whether the response is cachable. This may be force-set to False
        by the Context if POST data was accessed. Otherwise it is writable by
        the application to define whether the response may be cached by the
        client.
        """
        return self._cachable and not self._force_no_cache

    @Cachable.setter
    def Cachable(self, value):
        self._cachable = Types.Typecasts.bool(value)

    @property
    def IfModifiedSince(self):
        """
        Access to the requests If-Modified-Since value. Can be None if not
        supplied or malformed.
        """
        return self._if_modified_since

    @property
    def PageNode(self):
        """
        The PyXWF node responsible for serving the page.
        """
        return self._pagenode

    @PageNode.setter
    def PageNode(self, value):
        self._pagenode = value

    @property
    def LastModified(self):
        """
        Current Last-Modified value based on the used resources (see
        :meth:`use_resource`). This will return None if no resources are used
        or one of them exposes a None value as LastModified (which implies
        uncachability).
        """
        return self._last_modified

    @property
    def CanUseXHTML(self):
        """
        Whether XHTML can be interpreted by the client. This is by default False
        and shall be identified by the request headers sent by the requesting
        entity.

        If this is False, the application handling the request represented by
        this Context, must not send XHTML responses.
        """
        self.add_vary("Accept")
        return self._can_use_xhtml

    @property
    def IsMobileClient(self):
        """
        Return whether the user agent is a mobile phone or similar. This can be
        overriden to disable mobile detection and force it to a static value.
        This is for example useful to decide about mobile-suited responses
        depending on the host name used in the request.
        """
        self.add_vary("User-Agent")
        return self._is_mobile_client

    @IsMobileClient.setter
    def IsMobileClient(self, value):
        self._is_mobile_client = Types.Typecasts.bool(value)

    @property
    def HTML5Support(self):
        """
        Return whether the User-Agent is supposed to support HTML5. This is
        used by the site to determine whether to apply a to-html4 backtransform.
        """
        self.add_vary("User-Agent")
        return self._html5_support

    @property
    def CacheControl(self):
        """
        The current contents of the Cache-Control header values.
        """
        return frozenset(self._cache_control)

    @property
    def Cookies(self):
        """
        Return a dictionary mapping cookie names to :class:`~Cookie` instances.
        """
        if self._cookies is None:
            self.add_vary("Cookie")
            self._require_cookies()
        return self._cookies

    @abc.abstractmethod
    def send_response(self, message):
        """
        Send the :class:`~PyXWF.Message.Message` object referred to by *message*
        as response. This will render the filelike behind :attr:`Out` invalid
        for use for writing. This must be implemented by a derived class.
        """

    def use_resource(self, resource):
        """
        Mark the use of a given resource (which is expected to be a
        :class:`~PyXWF.Resource.Resource` instance) to build the response.
        This will later be regarded when calculating the Last-Modified value
        of the response, and thus whether the full response needs to be
        created.

        The resource is also asked to recheck its Last-Modified value and reload
        if neccessary, so this is a possible costy operation. However, a
        resource will never be asked twice during the same request.
        """
        if resource in self._used_resources:
            return
        self._used_resources.add(resource)
        resource.threadsafe_update()
        last_modified = resource.LastModified
        if last_modified is not None:
            if self._last_modified is not None:
                self._last_modified = max(self._last_modified, last_modified)
            else:
                self._last_modified = last_modified

    def use_resources(self, resources):
        """
        Marks multiple resources for use. This requires *resources* to be an
        iterable of Resources.
        """
        collections.deque(map(self.use_resource, resources), 0)

    def iter_resources(self):
        """
        Returns an iterator over the resources used to build the response.
        """
        return iter(self._used_resources)

    def check_not_modified(self):
        """
        Check whether the current Last-Modified value (based on the used
        resources, see :meth:`use_resource`) is older or equal to the
        If-Modified-Since value.

        If so, and if caching is not disabled, a
        :class:`~PyXWF.Errors.NotModified` is thrown.
        """
        if not self.Cachable:
            return
        last_modified = self.LastModified
        if last_modified is None:
            return
        if self.IfModifiedSince is None:
            return
        self.add_vary("If-Modified-Since")
        if self.LastModified <= self.IfModifiedSince:
            raise Errors.NotModified()

    def check_acceptable(self, content_type):
        """
        Check whether the given *content_type* (which must be either a
        :class:`basestring` or a :class:`~PyXWF.AcceptHeaders.Preference`
        instance) is acceptable by the client.

        Raise :class:`~PyXWF.Errors.NotAcceptable` if not.
        """
        if self._accept is None:
            return
        if len(self._accept) == 0:
            return
        if isinstance(content_type, basestring):
            content_type = AcceptHeaders.AcceptPreference.from_header_section(content_type)
        if self._accept.get_quality(content_type) <= 0.:
            raise Errors.NotAcceptable()

    def add_cache_control(self, token):
        """
        Add *token* to the set of Cache-Control HTTP tokens. Token must be a
        valid Cache-Control response value according to HTTP/1.1 (this is not
        enforced though (yet)).
        """
        self._cache_control.add(token.lower())

    def add_vary(self, field_name):
        """
        Add a HTTP header field name to the Vary HTTP response. *field_name* must
        be a valid HTTP/1.1 header name and will be lower-cased.
        """
        self._vary.add(field_name.lower())

    def set_response_header(self, header, value):
        """
        Set the value of the HTTP/1.1 response header *header* to *value*. Both
        are forced into non-unicode strings as per wsgi specification.
        """
        self._response_headers[str(header).lower()] = str(value)

    def clear_response_header(self, header):
        """
        Clear the value from the response header *header*, if any.
        """
        try:
            del self._response_headers[header.lower()]
        except KeyError:
            pass

    def set_response_content_type(self, mimetype, charset):
        """
        Set the content type of the response according to *mimetype* and
        *charset*. Charset may be :data:`None` or the empty string if it should
        be omitted.
        """
        if charset:
            self.set_response_header(b"Content-Type", b"{0}; charset={1}".format(mimetype, charset))
        else:
            self.set_response_header(b"Content-Type", str(mimetype))

    def send_empty_response(self, status):
        """
        Send an empty response with the HTTP status *status*. *status* may be
        either a :class:`~PyXWF.Errors.HTTPStatusBase` descendant class or
        instance.
        """
        return self.send_response(Message.EmptyMessage(status=status))

    def set_cookie(self, cookie):
        """
        Add the given :class:`~Cookie` *cookie* to the list of cookies to be
        sent with the response.
        """
        self._cookies.append(cookie)
