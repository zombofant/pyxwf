import re, os

import PyWeb.Registry as Registry
import PyWeb.Namespaces as NS
import PyWeb.Errors as Errors
import PyWeb.Types as Types

class HostNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/tweaks/host"

class HostRedirect(object):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(HostNS)
    tweakNames = ["redirect"]

    def __init__(self, site):
        super(HostRedirect, self).__init__()
        site.hooks.register("handle.pre-lookup", self.redirect)
        self.site = site
        redirects = self._tweaks["redirect"]

        self.redirects = [self._redirectFromET(node) for node in redirects]

    def _redirectFromET(self, node):
        srcName = Types.Typecasts.unicode(Types.NotNone(node.get("src")))
        dstName = Types.Typecasts.unicode(Types.NotNone(node.get("dest")))
        kind = Types.DefaultForNone(Errors.Found, Types.EnumMap({
            "301": Errors.MovedPermanently,
            "permanent": Errors.MovedPermanently,
            "302": Errors.Found,
            "found": Errors.Found,
            "303": Errors.SeeOther,
            "see-other": Errors.SeeOther,
            "307": Errors.TemporaryRedirect,
            "temporary": Errors.TemporaryRedirect
        }))(node.get("method"))
        return (srcName, dstName, kind)

    def redirect(self, ctx):
        for src, dst, kind in self.redirects:
            if ctx.HostName == src:
                path = "{2}://{0}{1}".format(
                    dst,
                    os.path.join(self.site.urlRoot, ctx.Path),
                    ctx.URLScheme
                )
                raise kind(newLocation=path, local=False)

class HostForceMobile(object):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(HostNS)
    tweakNames = ["force-mobile"]

    _hostNameType = Types.NotNone

    def __init__(self, site):
        super(HostForceMobile, self).__init__()
        site.hooks.register("handle.pre-lookup", self.forceMobile)
        self.site = site

        self.hosts = dict(
            (self._hostNameType(node.get("host")),
             Types.Typecasts.bool(node.get("mobile", True))
            ) for node in self._tweaks["force-mobile"])

    def forceMobile(self, ctx):
        try:
            ctx.IsMobileClient = self.hosts[ctx.HostName]
            print("host-based mobileness set to {0}".format(ctx.IsMobileClient))
        except KeyError:
            pass
