import re, os, logging

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
    tweak_names = ["redirect"]

    def __init__(self, site):
        super(HostRedirect, self).__init__(site,
            tweak_ns=self.namespace,
            tweak_names=self.tweak_names
        )
        site.hooks.register("handle.pre-lookup", self.redirect)
        self.redirects = []

    def tweak(self, node):
        self.redirects.append(self._redirect_from_ET(node))

    def _redirect_from_ET(self, node):
        src_name = Types.Typecasts.unicode(Types.NotNone(node.get("src")))
        dst_name = Types.Typecasts.unicode(Types.NotNone(node.get("dest")))
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
        return (src_name, dst_name, kind)

    def redirect(self, ctx):
        for src, dst, kind in self.redirects:
            if ctx.HostName == src:
                path = "{2}://{0}{1}".format(
                    dst,
                    os.path.join(self.Site.urlroot, ctx.Path),
                    ctx.URLScheme
                )
                raise kind(location=path, local=False)

class HostForceMobile(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(HostNS)
    tweak_names = ["force-mobile"]

    _host_name_type = Types.NotNone

    def __init__(self, site):
        super(HostForceMobile, self).__init__(site,
            tweak_ns=self.namespace,
            tweak_names=self.tweak_names
        )
        site.hooks.register("handle.pre-lookup", self.force_mobile)
        self.hosts = {}

    def tweak(self, node):
        key = self._host_name_type(node.get("host"))
        force_mobile = Types.Typecasts.bool(node.get("mobile", True))
        self.hosts[key] = force_mobile

    def force_mobile(self, ctx):
        try:
            ctx.IsMobileClient = self.hosts[ctx.HostName]
            logging.debug("host-based mobileness set to {0}".format(ctx.IsMobileClient))
        except KeyError:
            pass
