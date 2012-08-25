from __future__ import unicode_literals, print_function

import operator, abc, collections, functools, logging, itertools
from fnmatch import fnmatch
from wsgiref.handlers import format_date_time

import PyXWF.Types as Types
import PyXWF.Errors as Errors
import PyXWF.TimeUtils as TimeUtils
import PyXWF.ContentTypes as ContentTypes

@functools.total_ordering
class Preference(object):
    """
    Represent a HTTP Header preference, for example:

        text/html;q=0.9

    would be constructed as:

        Preference("text/html", 0.9)

    Preference objects compare according to the q value assigned to them.
    """
    @classmethod
    def fromHeaderSection(cls, value, dropParameters=False, index=0):
        parts = value.lower().split(";")
        header = parts[0].strip()
        parameters = parts[1:]

        q = 1.
        typeParameters = {}
        for parameter in parameters:
            parameter = parameter.strip()
            name, _, arg = parameter.partition("=")
            if name == "q":
                try:
                    q = float(arg)
                except ValueError:
                    q = 0.
                break
            elif dropParameters:
                continue
            if not _:
                typeParameters[name] = None
            else:
                typeParameters[name] = arg.strip()

        return cls(header, q, parameters=typeParameters, index=index)

    @classmethod
    def listFromHeader(cls, headerValue, dropParameters=False):
        """
        Parse a HTTP formatted list of preferences like the following:

            text/html;q=1.0, application/xml;q=0.9, */*
        """
        try:
            # parse preferences
            prefs = (cls.fromHeaderSection(section, dropParameters=dropParameters, index=i)
                     for i, section in enumerate(headerValue.split(",")))
            # sort the result
            # don't drop q=0, as it might be used to disable certain ranges
            prefs = sorted(prefs,
                    reverse=True,
                    key=Preference.rfcCompliantKey)
        except ValueError:
            print("Parsing of preference list failed on following input: {0}".format(preferences))
            prefs = []
        return prefs

    def __init__(self, value, q, parameters={}, index=0):
        self.value = value
        # the more asterisks, the lower the precedence
        self.precedence = -value.count("*")
        self.q = q
        self.typeParameters = parameters
        self.index = index
        self.rfcKey = (self.precedence, self.q, len(self.typeParameters), -index)
        self.fullKey = (self.precedence, self.q, self.value, tuple(self.typeParameters.items()))

    def __unicode__(self):
        return ";".join(itertools.chain(
            [self.value],
            ("{0}={1}".format(key, value) for key, value in self.typeParameters.items())
        ))

    def __repr__(self):
        return "{0};q={1:.2f}".format(unicode(self), self.q)

    def __repr__(self):
        return unicode(self)

    def __eq__(self, other):
        try:
            return self.fullKey == other.fullKey
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.fullKey != other.fullKey
        except AttributeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.fullKey < other.fullKey
        except AttributeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.fullKey <= other.fullKey
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return hash(self.fullKey)

    def match(self, otherPref, allowWildcard=True):
        if isinstance(otherPref, Preference):
            wildcardPenalty, _, q = self.match(otherPref.value)
            keysUsed = 0
            if q <= 0:
                return (wildcardPenalty, 0, q)
            try:
                remainingKeys = set(otherPref.typeParameters.keys())
                for key, value in self.typeParameters.items():
                    if otherPref.typeParameters[key] != value:
                        return (0, 0, 0)
                    keysUsed += 1
                    remainingKeys.discard(key)
                if len(remainingKeys) > 0 and not allowWildcard:
                    return (0, 0, 0)
            except KeyError:
                return (0, 0, 0)
            return (wildcardPenalty, keysUsed, q)
        else:
            wildcardPenalty = self.precedence
            if allowWildcard:
                if fnmatch(otherPref, self.value):
                    return (wildcardPenalty, 0, self.q)
                else:
                    return (0, 0, 0)
            else:
                if otherPref == self.value:
                    return (0, 0, self.q)
                else:
                    return (0, 0, 0)

    rfcCompliantKey = operator.attrgetter("rfcKey")

class Context(object):
    """
    The context of a request. It is passed around when retrieving the Document
    from the Node tree and can be used to store custom data. All the properties
    of the framework are named with a capital first letter or prefixed with an
    underscore, so you're safe to use all other names.
    """
    __metaclass__ = abc.ABCMeta

    htmlPreferences = [
        # prefer delivery of XHTML (no conversion required)
        Preference("application/xhtml+xml", 1.0),
        Preference("text/html", 0.9)
    ]

    charsetPreferences = [
        # prefer UTF-8, then go through the other unicode encodings in
        # ascending order of size. prefer little-endian over big-endian
        # encodings
        Preference("utf-8", 1.0),
        Preference("utf-16le", 0.95),
        Preference("utf-16be", 0.9),
        Preference("ucs-2le", 0.85),
        Preference("ucs-2be", 0.8),
        Preference("utf-32le", 0.75),
        Preference("utf-32be", 0.7),
    ]

    userAgentHTML5Support = {
        "ie": 9.0,
        "firefox": 4.0,
        "chrome": 6.0,
        "safari": 5.0,
        "opera": 11.1
    }

    def __init__(self, method, path, outfile):
        self._method = method
        self._path = path
        self._outfile = outfile
        self._remainingPath = None
        self._queryData = None
        self._postData = None
        self._cachePath = path
        self._cacheTokens = set()
        self._forceNoCache = False
        self._cachable = True
        self._ifModifiedSince = None
        self._pageNode = None
        self._usedResources = set()
        self._lastModified = None
        self._canUseXHTML = False
        self._cacheControl = set()
        self._html5Support = False
        self._vary = set(["host"])  # this is certainly used ;)
        self._accept = None
        self._isMobileClient = False
        self._responseHeaders = {}

    def _requireQuery(self):
        """
        Extract query string from the web frameworks transaction and make it
        accessible. Also make a note that the query string was used in this
        request and is thus needs to be appended to the cache path.
        """
        raise NotImplemented()

    def _requirePost(self):
        """
        Extract the post data from the request and make it available at
        :prop:`PostData`. This disables caching of the response altogether.
        """
        self._forceNoCache = True

    def _setCacheHeaders(self):
        if self.Cachable:
            lastModified = self.LastModified
            if lastModified is not None:
                self.addCacheControl("must-revalidate")
                self.setResponseHeader("Last-Modified",
                    format_date_time(TimeUtils.toTimestamp(lastModified)))
        else:
            self.addCacheControl("no-cache")
        if len(self._cacheControl) > 0:
            self.setResponseHeader("Cache-Control", ",".join(self._cacheControl))
        if len(self._vary) > 0:
            self.setResponseHeader("Vary", ",".join(self._vary))

    def _determineHTMLContentType(self):
        logging.debug("Accept: {0}".format(", ".join(map(str, self._accept))))
        htmlContentType = self.getPreferenceToUse(
            self._accept,
            self.htmlPreferences,
            matchWildcard=False
        )
        self._canUseXHTML = htmlContentType == ContentTypes.xhtml
        logging.debug("CanUseXHTML: {0}".format(self._canUseXHTML))
        return htmlContentType

    def parseAccept(self, headerValue):
        return Preference.listFromHeader(headerValue)

    def parseAcceptCharset(self, headerValue):
        prefs = Preference.listFromHeader(headerValue, dropParameters=True)

        starCount = sum(map(lambda x: 1 if x.value == "*" else 0, prefs))
        if starCount == 0:
            # according to HTTP/1.1 spec, we _have_ to add iso-8859-1 if no "*"
            # is in the list
            prefs.append(Preference("iso-8859-1", 1.0, index=len(prefs)))
            prefs.sort(key=Preference.rfcCompliantKey)

        return prefs

    def getEncodedBody(self, message, remotePreferences=[]):
        candidates = self.getPreferenceCandidates(remotePreferences,
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
            logging.debug("Accept-Charset: {0}".format(", ".join(map(str, remotePreferences))))
            raise Errors.NotAcceptable()

    def getPreferenceCandidates(self, remotePreferences, ownPreferences,
            matchWildcard=True,
            includeNonMatching=False,
            takeEverythingOnEmpty=True):
        if len(remotePreferences) == 0:
            if takeEverythingOnEmpty:
                # everything is acceptable
                return list(map(lambda x: (x.q, x.value), ownPreferences))
            else:
                return []

        candidates = dict()
        for remPref in remotePreferences:
            for ownPref in ownPreferences:
                sortKey = remPref.match(ownPref, allowWildcard=matchWildcard)
                penalty, keys, q = sortKey
                if q > 0.:
                    value = unicode(ownPref)
                    sortKey = penalty, keys, q, ownPref.q, -remPref.index
                elif includeNonMatching and remPref.precedence == 0:
                    # we must not add values with precedence != 0
                    value = unicode(remPref)
                    sortKey = remPref.precedence, 0, remPref.q, 0, -remPref.index
                else:
                    continue
                try:
                    oldKey = candidates[value]
                    if oldKey < sortKey:
                        candidates[value] = sortKey
                except KeyError:
                    candidates[value] = sortKey

        candidates = sorted(
            ((q, pref) for pref, q in candidates.iteritems()),
            key=operator.itemgetter(0))
        candidates = [(q, pref) for (prec, keys, q, q2, index), pref in candidates]
        return candidates

    def getPreferenceToUse(self, remotePreferences,
            ownPreferences, matchWildcard=True):
        candidates = self.getPreferenceCandidates(remotePreferences,
            ownPreferences,
            matchWildcard=matchWildcard,
            includeNonMatching=False)
        try:
            # return the candidate with highest rating. return the preference
            # object from our list, as that's guaranteed to have a fully
            # qualified content type
            return candidates.pop()[1]
        except IndexError:
            # no candidates
            return None

    @classmethod
    def userAgentSupportsHTML5(cls, userAgent, version):
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
        The URL path for the request.
        """
        return self._path

    @property
    def FullURI(self):
        """
        The URL path for the request.
        """
        return self._fullURI

    @property
    def HostName(self):
        return self._hostName

    @property
    def URLScheme(self):
        return self._scheme

    Path = RequestPath

    @property
    def Out(self):
        """
        A filelike where the response shall go to.
        """
        return self._outfile

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
        if POST data was accessed.
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
        Return whether the user agent is a mobile phone or similar.
        """
        self.addVary("User-Agent")
        return self._isMobileClient

    @IsMobileClient.setter
    def IsMobileClient(self, value):
        self._isMobileClient = Types.Typecasts.bool(value)
        print(self._isMobileClient)

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
        Send the :cls:`Message.Message` object referred to by *message* as
        response. This will render the filelike behind :prop:`Out` invalid for
        use for writing. This must be implemented by a derived class.
        """

    def useResource(self, resource):
        """
        Mark the use of a given resource to build the response. This will later
        be regarded when calculating the Last-Modified value of the response,
        and thus whether the full response needs to be created.

        The resource is also asked to recheck its Last-Modified value and reload
        if neccessary, so this is a possible costy operation. However, a
        resource will never be asked twice.
        """
        if resource in self._usedResources:
            return
        self._usedResources.add(resource)
        resource.update()
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

        If so, and if caching is not disabled, a :cls:`Errors.HTTP.NotModified`
        is thrown.
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
        if self._accept is None:
            return
        if len(self._accept) == 0:
            return
        for pref in self._accept:
            if pref.value == contentType or fnmatch(contentType, pref.value):
                return
        else:
            raise Errors.NotAcceptable()

    def addCacheControl(self, token):
        """
        Add *token* to the list of Cache-Control HTTP tokens.
        """
        self._cacheControl.add(token)

    def addVary(self, fieldName):
        self._vary.add(fieldName.lower())

    def setResponseHeader(self, header, value):
        self._responseHeaders[header.lower()] = [value]

    def appendResponseHeader(self, header, value):
        self._responseHeaders.setdefault(header.lower(), []).append(value)

    def setResponseContentType(self, mimeType, charset):
        if charset:
            self.setResponseHeader("Content-Type", "{0}; charset={1}".format(mimeType, charset))
        else:
            self.setResponseHeader("Content-Type", mimeType)
