import re, os

import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.Tweaks as Tweaks

class HostNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/tweaks/host"

class HostRedirect(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(HostNS)
    tweakNames = ["redirect"]

    def __init__(self, site):
        super(HostRedirect, self).__init__(site,
            tweakNS=self.namespace,
            tweakNames=self.tweakNames
        )
        site.hooks.register("handle.pre-lookup", self.redirect)
        self.redirects = []

    def tweak(self, node):
        self.redirects.append(self._redirectFromET(node))

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

class HostForceMobile(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(HostNS)
    tweakNames = ["force-mobile"]

    _hostNameType = Types.NotNone

    def __init__(self, site):
        super(HostForceMobile, self).__init__(site,
            tweakNS=self.namespace,
            tweakNames=self.tweakNames
        )
        site.hooks.register("handle.pre-lookup", self.forceMobile)
        self.hosts = {}

    def tweak(self, node):
        key = self._hostNameType(node.get("host"))
        forceMobile = Types.Typecasts.bool(node.get("mobile", True))
        self.hosts[key] = forceMobile

    def forceMobile(self, ctx):
        try:
            ctx.IsMobileClient = self.hosts[ctx.HostName]
            print("host-based mobileness set to {0}".format(ctx.IsMobileClient))
        except KeyError:
            pass
