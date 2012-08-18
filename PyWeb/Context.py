from __future__ import unicode_literals

import operator, abc, collections, functools
from fnmatch import fnmatch

import PyWeb.Types as Types
import PyWeb.Errors as Errors

@functools.total_ordering
class Preference(object):
    """
    Represent a HTTP Header preference, for example:

        text/html;q=0.9

    would be constructed as:

        Preference("text/html", 0.9)

    Preference objects compare according to the q value assigned to them.
    """
    def __init__(self, value, q):
        self.value = value
        self.q = q

    def __le__(self, other):
        try:
            return self.q <= other.q
        except AttributeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.q < other.q
        except AttributeError:
            return NotImplemented

    def __eq__(self, other):
        try:
            return self.q == other.q
        except AttributeError:
            return NotImplemented

    def __unicode__(self):
        return "{0};q={1:.2f}".format(self.value, self.q)

    def __repr__(self):
        return unicode(self)

class Context(object):
    """
    The context of a request. It is passed around when retrieving the Document
    from the Node tree and can be used to store custom data. All the properties
    of the framework are named with a capital first letter or prefixed with an
    underscore, so you're safe to use all other names.
    """
    __metaclass__ = abc.ABCMeta

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

    @classmethod
    def parsePreferencesList(cls, preferences):
        """
        Parse a HTTP formatted list of preferences like the following:

            text/html;q=1.0, application/xml;q=0.9, */*
        """
        prefs = (s.strip().lower().partition(';')
                    for s in preferences.split(","))
        prefs = (Preference(value, float(q[2:]) if len(q) > 0 else 1.0)
                    for (value, sep, q) in prefs
                    if not (len(q) > 0 and float(q[2:])==0) and len(value) > 0)
        prefs = sorted(prefs, reverse=True)
        return prefs

    @classmethod
    def getCharsetToUse(cls, prefList, ownPreferences):
        use = None
        q = None
        if len(prefList) == 0:
            return ownPreferences[0]
        for item in prefList:
            if q is None:
                q = item.q
            if use is None:
                use = item.value
            if item.q < q:
                break
            if item.value in ownPreferences:
                return item.value
            if item.value == "*" and use is None:
                use = ownPreferences[0]
        if use is None:
            use = ownPreferences[0]
        return use

    @classmethod
    def getContentTypeToUse(cls, prefList, ownPreferences):
        if len(prefList) == 0:
            return None

        use = None
        for pref in ownPreferences:
            for item in prefList:
                if item.value == pref:
                    return item.value
                if use is None and fnmatch(pref, item.value):
                    use = pref
        return use

    @classmethod
    def userAgentSupportsHTML5(cls, userAgent, version):
        try:
            minVersion = cls.userAgentHTML5Support[userAgent]
            return version >= minVersion
        except KeyError:
            return False

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
        self._cachable = Typecasts.Types.bool(value)

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
        The PyWeb node responsible for serving the page.
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
        return self._canUseXHTML

    @property
    def HTML5Support(self):
        """
        Return whether the User-Agent is supposed to support HTML5. This is
        used by the site to determine whether to apply a to-html4 backtransform.
        """
        return self._html5Support

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
            self.addCacheControl("no-cache")
            return
        lastModified = self.LastModified
        if lastModified is None:
            return
        self.addCacheControl("must-revalidate")
        if self.IfModifiedSince is None:
            return
        if self.LastModified <= self.IfModifiedSince:
            raise Errors.NotModified()

    def checkAcceptable(self, contentType):
        pass

    def addCacheControl(self, token):
        """
        Add *token* to the list of Cache-Control HTTP tokens.
        """
        self._cacheControl.add(token)
