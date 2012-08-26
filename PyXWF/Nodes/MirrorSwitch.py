from __future__ import unicode_literals
import os
import httplib, random, urllib

import PyXWF.Nodes as Nodes
import PyXWF.Types as Types
import PyXWF.Registry as Registry
import PyXWF.Navigation as Navigation
import PyXWF.Document as Document
import PyXWF.Errors as Errors
import PyXWF.Resource as Resource
import PyXWF.Namespaces as NS

class MirrorNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/nodes/mirror"

class Mirror(object):
    def __init__(self, node):
        self.host = Types.NotNone(node.get("host"))
        self.noSSL = Types.Typecasts.bool(node.get("no-ssl", False))
        self.path = Types.NotNone(node.get("path"))
        self.port = Types.NumericRange(int, 1, 65535)(node.get("port", 80))
        self.sslPort = Types.NumericRange(int, 1, 65535)(node.get("ssl-port", 443))

    def test(self, fileName):
        path = self.path + fileName
        if self.noSSL:
            conn = httplib.HTTPConnection(self.host, self.port)
        else:
            conn = httplib.HTTPSConnection(self.host, self.sslPort)
        try:
            urlEncoded = urllib.quote(path.encode("utf-8"))
            conn.request("HEAD", urlEncoded)
            response = conn.getresponse()
            status = response.status
        finally:
            conn.close()

        if status == 200:
            return "{0}{1}".format(self.host, urlEncoded)
        else:
            return None

    def __unicode__(self):
        return "Mirror at {0}".format(self.host)

class MirrorSwitch(Nodes.Node, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = str(MirrorNS)
    names = ["switch"]

    def __init__(self, site, parent, node):
        super(MirrorSwitch, self).__init__(site, parent, node)
        self._navDisplay = Types.DefaultForNone(-1, Navigation.DisplayMode)\
                                                (node.get("nav-display"))
        self._navTitle = node.get("nav-title", "mirror switch (should remove me from nav probably)")

        self.mirrors = [Mirror(mnode) for mnode in node.findall(MirrorNS.host)]

    def resolvePath(self, ctx, relPath):
        toTry = list(self.mirrors)
        random.shuffle(toTry)
        for mirror in toTry:
            postSchemeURL = mirror.test(relPath)
            if postSchemeURL is not None:
                scheme = ctx.URLScheme
                if mirror.noSSL:
                    scheme = "http"
                ctx.Cachable = False
                raise Errors.Found(
                    location="{0}://{1}".format(scheme, postSchemeURL),
                    local=False
                )
        raise Errors.NotFound()

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self._navTitle

    def getDisplay(self):
        return self._navDisplay

    def getRepresentative(self):
        return self
