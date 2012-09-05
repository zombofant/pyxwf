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
        self.no_ssl = Types.Typecasts.bool(node.get("no-ssl", False))
        self.path = Types.NotNone(node.get("path"))
        self.port = Types.NumericRange(int, 1, 65535)(node.get("port", 80))
        self.ssl_port = Types.NumericRange(int, 1, 65535)(node.get("ssl-port", 443))

    def test(self, filename):
        path = self.path + filename
        if self.no_ssl:
            conn = httplib.HTTPConnection(self.host, self.port)
        else:
            conn = httplib.HTTPSConnection(self.host, self.ssl_port)
        try:
            urlencoded = urllib.quote(path.encode("utf-8"))
            conn.request("HEAD", urlencoded)
            response = conn.getresponse()
            status = response.status
        finally:
            conn.close()

        if status == 200:
            return "{0}{1}".format(self.host, urlencoded)
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
        self._navdisplay = Types.DefaultForNone(-1, Navigation.DisplayMode)\
                                                (node.get("nav-display"))
        self._navtitle = node.get("nav-title", "mirror switch (should remove me from nav probably)")

        self.mirrors = [Mirror(mnode) for mnode in node.findall(MirrorNS.host)]

    def resolve_path(self, ctx, relpath):
        totry = list(self.mirrors)
        random.shuffle(totry)
        for mirror in totry:
            schemeless_url = mirror.test(relpath)
            if schemeless_url is not None:
                scheme = ctx.URLScheme
                if mirror.no_ssl:
                    scheme = "http"
                ctx.Cachable = False
                raise Errors.Found(
                    location="{0}://{1}".format(scheme, schemeless_url),
                    local=False
                )
        raise Errors.NotFound()

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self._navtitle

    def get_display(self):
        return self._navdisplay

    def get_representative(self):
        return self
