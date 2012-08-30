import re

import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Tweaks as Tweaks

class _NS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/tweaks/global-redirect"

class GlobalRedirect(object):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(_NS)
    tweakNames = ["redirect"]

    def __init__(self, site):
        super(GlobalRedirect, self).__init__()
        self.site.hooks.register("handle.pre-lookup", self.redirect)
        redirects = self._tweaks["redirect"].findall(self.NS.redirect)

        self.redirects = [self._redirectFromET(node) for node in redirects]

    def _redirectFromET(self, node):
        sourcePatt = Typecasts.Types.unicode(Typecasts.NotNone(node.get("src")))
        destPatt = Typecasts.Types.unicode(Typecasts.NotNone(node.get("dest")))
        kind = Typecasts.DefaultForNone(Errors.Found, Typecasts.EnumMap({
            "301": Errors.MovedPermanently,
            "302": Errors.Found,
            "303": Errors.SeeOther,
            "307": Errors.TemporaryRedirect
        }))(node.get("method"))

        return (re.compile(sourcePatt), destPatt, kind)

    def redirect(self, ctx):
        path = ctx.Path
        for src, dst, kind in self.redirects:
            m = src.match(path)
            if m:
                raise kind(location=self._replace(m, dst))

GlobalRedirect.NS = _NS
