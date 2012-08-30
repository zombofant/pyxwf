# encoding=utf-8
from __future__ import unicode_literals, print_function

import operator, abc, collections, functools, logging, itertools
from fnmatch import fnmatch

import PyXWF.Types as Types
import PyXWF.Errors as Errors
import PyXWF.TimeUtils as TimeUtils
import PyXWF.ContentTypes as ContentTypes
import PyXWF.HTTPUtils as HTTPUtils
import PyXWF.AcceptHeaders as AcceptHeaders
import PyXWF.Message as Message

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

    htmlPreferences = [
        # prefer delivery of XHTML (no conversion required)
        AcceptHeaders.AcceptPreference("application/xhtml+xml", 1.0),
        AcceptHeaders.AcceptPreference("text/html", 0.9)
    ]

    charsetPreferences = [
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

    userAgentHTML5Support = {
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
        # :meth:`_requireQuery` )
        self._queryData = None

        # query data, as a python dict (can be initialized lazily in
        # :meth:`_requirePost` )
        self._postData = None

        # datetime object representing the value of the incoming
        # If-Modified-Since header, if any. Otherwise None
        self._ifModifiedSince = None

        # :class:`AcceptPreferenceList` instance
        self._accept = None

        # :class:`CharsetPreferenceList` instance
        self._acceptCharset = None

        # :class:`LanguagePreferenceList` instance
        self._acceptLanguage = None

        # will be set to True if POST data was requested (can be avoided by not
        # calling super()._requirePost when overriding _requirePost)
        self._forceNoCache = False

        # these are backing values for the properties below. See their
        # docstrings for further information
        self._cachable = True
        self._pageNode = None
        self._usedResources = set()
        self._lastModified = None
        self._canUseXHTML = False
        self._cacheControl = set()
        self._html5Support = False
        self._isMobileClient = False
        self._responseHeaders = {}
        self._vary = set(["host"])

    def _requireQuery(self):
        """
        Extract query string from the web frameworks transaction and make it
        accessible. Also make a note that the query string was used in this
        request and is thus needs to be appended to the cache path.

        .. note::
            This must be overridden when implementing a Context for a specific
            web backend.
        """
        raise NotImplemented()

    def _requirePost(self):
        """
        Extract the post data from the request and make it available at
        :attr:`PostData`. This disables caching of the response altogether.

        .. note::
            This must be overridden when implementing a Context for a specific
            web backend.
        """
        self._forceNoCache = True

    def _setCacheStatus(self):
        """
        Use the values of :attr:`Cachable` and :attr:`LastModified` to set up
        the response headers which relate to caching. This may change the value
        of the ``Last-Modified`` header and will add a cache control token.
        """
        if self.Cachable:
            lastModified = self.LastModified
            if lastModified is not None:
                self.addCacheControl("must-revalidate")
                self.setResponseHeader("Last-Modified",
                    HTTPUtils.formatHTTPDate(lastModified))
        else:
            self.addCacheControl("no-cache")

    def _determineHTMLContentType(self):
        """
        Use the :class:`~PyXWF.AcceptHeaders.AcceptPreferenceList` instance to
        figure out whether the client properly supports XHTML.

        Will set :attr:`~.CanUseXHTML` to True if the best match for all HTML
        content types is the XHTML content type.
        """
        logging.debug("Accept: {0}".format(", ".join(map(str, self._accept))))
        htmlContentType = self._accept.bestMatch(
            self.htmlPreferences,
            matchWildcard=False
        )
        self._canUseXHTML = htmlContentType == ContentTypes.xhtml
        logging.debug("CanUseXHTML: {0}".format(self._canUseXHTML))
        return htmlContentType

    def _setPropertyHeaders(self):
        """
        Convert :attr:`~.Vary` and :attr:`~.CacheControl` into HTTP headers and
        add them to the response headers.
        """
        if self._vary:
            self.setResponseHeader(b"vary", b",".join(self._vary))
        else:
            self.clearResponseHeader(b"vary")

        if self._cacheControl:
            self.setResponseHeader(b"cache-control", b",".join(self._cacheControl))
        else:
            self.clearResponseHeader(b"cache-control")

    def parseAccept(self, headerValue):
        """
        Parse *headerValue* as value of an HTTP ``Accept`` header and return the
        resulting :class:`~PyXWF.AcceptHeaders.AcceptPreferenceList` instance.
        """
        prefs = AcceptHeaders.AcceptPreferenceList()
        prefs.appendHeader(headerValue)
        return prefs

    def parseAcceptCharset(self, headerValue):
        """
        Parse *headerValue* as value of an HTTP ``Accept-Charset`` header and
        return the resulting :class:`~PyXWF.AcceptHeaders.CharsetPreferenceList`
        instance.
        """
        prefs = AcceptHeaders.CharsetPreferenceList()
        prefs.appendHeader(headerValue)
        prefs.injectRFCValues()
        return prefs

    def getEncodedBody(self, message):
        """
        Try to get the best encoded version of the
        :class:`~PyXWF.Message.Message` instance *message*.

        Use the contents of :attr:`_acceptCharset` (the parsed
        ``Accept-Charset`` HTTP header) to figure out which charsets the client
        prefers. Then mix in what charsets _we_ like to deliver and get the
        best match, giving priority to the clients wishes.

        If no matching encoding can be found,
        :class:`~PyXWF.Errors.NotAcceptable` is raised.
        """
        candidates = self._acceptCharset.getCandidates(
            self.charsetPreferences,
            matchWildcard=True,
            includeNonMatching=True,
            takeEverythingOnEmpty=True)

        # to prevent denial of service, we only test the first five encodings
        for q, encoding in itertools.islice(reversed(candidates), 0, 5):
            try:
                message.Encoding = encoding
                return message.getEncodedBody()
            except UnicodeEncodeError:
                pass
        else:
            # we try to serve the client UTF-8 and log a warning
            logging.warning("No charset the client presented us worked to encode the message, returning 406 Not Acceptable")
            logging.debug("Accept-Charset: {0}".format(", ".join(map(str, self._acceptCharset))))
            raise Errors.NotAcceptable()

    @classmethod
    def userAgentSupportsHTML5(cls, userAgent, version):
        """
        Guess whether the user agent *userAgent* with version *version* (as
        obtained for example from :func:`PyXWF.utils.guessUserAgent`) can deal
        with HTML5. This is only more or less accurate for the popular browsers.
        Everyone else will just be served HTML5.
        """
        try:
            minVersion = cls.userAgentHTML5Support[userAgent]
            return version >= minVersion
        except KeyError:
            return True  # we assume the best ... let them burn

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
        return self._fullURI

    @property
    def HostName(self):
        """
        Host name the request was sent to.
        """
        return self._hostName

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
        self._requireQuery()
        return self._queryData

    @property
    def PostData(self):
        """
        Access to the POST data of the request. Accessing this property will
        disable caching of the response.
        """
        self._requirePost()
        return self._postData

    @property
    def RemainingPath(self):
        """
        Path suffix which was not interpreted during resolution of the path
        inside the node tree. This may be useful for redirects.
        """
        return self._remainingPath

    @RemainingPath.setter
    def RemainingPath(self, value):
        self._remainingPath = Typecasts.Types.unicode(value)

    @property
    def Cachable(self):
        """
        Set whether the response is cachable. This may be force-set to False
        by the Context if POST data was accessed. Otherwise it is writable by
        the application to define whether the response may be cached by the
        client.
        """
        return self._cachable and not self._forceNoCache

    @Cachable.setter
    def Cachable(self, value):
        self._cachable = Types.Typecasts.bool(value)

    @property
    def IfModifiedSince(self):
        """
        Access to the requests If-Modified-Since value. Can be None if not
        supplied or malformed.
        """
        return self._ifModifiedSince

    @property
    def PageNode(self):
        """
        The PyXWF node responsible for serving the page.
        """
        return self._pageNode

    @property
    def LastModified(self):
        """
        Current Last-Modified value based on the used resources (see
        :meth:`useResource`). This will return None if no resources are used
        or one of them exposes a None value as LastModified (which implies
        uncachability).
        """
        return self._lastModified

    @property
    def CanUseXHTML(self):
        """
        Whether XHTML can be interpreted by the client. This is by default False
        and shall be identified by the request headers sent by the requesting
        entity.

        If this is False, the application handling the request represented by
        this Context, must not send XHTML responses.
        """
        self.addVary("Accept")
        return self._canUseXHTML

    @property
    def IsMobileClient(self):
        """
        Return whether the user agent is a mobile phone or similar. This can be
        overriden to disable mobile detection and force it to a static value.
        This is for example useful to decide about mobile-suited responses
        depending on the host name used in the request.
        """
        self.addVary("User-Agent")
        return self._isMobileClient

    @IsMobileClient.setter
    def IsMobileClient(self, value):
        self._isMobileClient = Types.Typecasts.bool(value)

    @property
    def HTML5Support(self):
        """
        Return whether the User-Agent is supposed to support HTML5. This is
        used by the site to determine whether to apply a to-html4 backtransform.
        """
        self.addVary("User-Agent")
        return self._html5Support

    @property
    def CacheControl(self):
        """
        The current contents of the Cache-Control header values.
        """
        return frozenset(self._cacheControl)

    @abc.abstractmethod
    def sendResponse(self, message):
        """
        Send the :class:`~PyXWF.Message.Message` object referred to by *message*
        as response. This will render the filelike behind :attr:`Out` invalid
        for use for writing. This must be implemented by a derived class.
        """

    def useResource(self, resource):
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
        if resource in self._usedResources:
            return
        self._usedResources.add(resource)
        resource.threadSafeUpdate()
        lastModified = resource.LastModified
        if lastModified is not None:
            if self._lastModified is not None:
                self._lastModified = max(self._lastModified, lastModified)
            else:
                self._lastModified = lastModified

    def useResources(self, resources):
        """
        Marks multiple resources for use. This requires *resources* to be an
        iterable of Resources.
        """
        collections.deque(map(self.useResource, resources), 0)

    def iterResources(self):
        """
        Returns an iterator over the resources used to build the response.
        """
        return iter(self._usedResources)

    def checkNotModified(self):
        """
        Check whether the current Last-Modified value (based on the used
        resources, see :meth:`useResource`) is older or equal to the
        If-Modified-Since value.

        If so, and if caching is not disabled, a
        :class:`~PyXWF.Errors.NotModified` is thrown.
        """
        if not self.Cachable:
            return
        lastModified = self.LastModified
        if lastModified is None:
            return
        if self.IfModifiedSince is None:
            return
        self.addVary("If-Modified-Since")
        if self.LastModified <= self.IfModifiedSince:
            raise Errors.NotModified()

    def checkAcceptable(self, contentType):
        """
        Check whether the given *contentType* (which must be either a
        :class:`basestring` or a :class:`~PyXWF.AcceptHeaders.Preference`
        instance) is acceptable by the client.

        Raise :class:`~PyXWF.Errors.NotAcceptable` if not.
        """
        if self._accept is None:
            return
        if len(self._accept) == 0:
            return
        if isinstance(contentType, basestring):
            contentType = AcceptHeaders.AcceptPreference.fromHeaderSection(contentType)
        if self._accept.getQuality(contentType) <= 0.:
            raise Errors.NotAcceptable()

    def addCacheControl(self, token):
        """
        Add *token* to the set of Cache-Control HTTP tokens. Token must be a
        valid Cache-Control response value according to HTTP/1.1 (this is not
        enforced though (yet)).
        """
        self._cacheControl.add(token.lower())

    def addVary(self, fieldName):
        """
        Add a HTTP header field name to the Vary HTTP response. *fieldName* must
        be a valid HTTP/1.1 header name and will be lower-cased.
        """
        self._vary.add(fieldName.lower())

    def setResponseHeader(self, header, value):
        """
        Set the value of the HTTP/1.1 response header *header* to *value*. Both
        are forced into non-unicode strings as per wsgi specification.
        """
        self._responseHeaders[str(header).lower()] = str(value)

    def clearResponseHeader(self, header):
        """
        Clear the value from the response header *header*, if any.
        """
        try:
            del self._responseHeaders[header.lower()]
        except KeyError:
            pass

    def setResponseContentType(self, mimeType, charset):
        """
        Set the content type of the response according to *mimeType* and
        *charset*. Charset may be :data:`None` or the empty string if it should
        be omitted.
        """
        if charset:
            self.setResponseHeader(b"Content-Type", b"{0}; charset={1}".format(mimeType, charset))
        else:
            self.setResponseHeader(b"Content-Type", str(mimeType))

    def sendEmptyResponse(self, status):
        """
        Send an empty response with the HTTP status *status*. *status* may be
        either a :class:`~PyXWF.Errors.HTTPStatusBase` descendant class or
        instance.
        """
        return self.sendResponse(Message.EmptyMessage(status=status))
