import re, logging

import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types

class UserAgentNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/tweaks/user-agent"

class ForceMobile(object):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(UserAgentNS)
    tweak_names = ["force-mobile"]

    def __init__(self, site):
        super(ForceMobile, self).__init__()
        site.hooks.register("handle.pre-lookup", self.force_mobile)
        self.site = site
        self.force_mobile = Types.Typecasts.bool(self._tweaks["force-mobile"][-1].get("mobile"))

    def force_mobile(self, ctx):
        ctx.IsMobileClient = self.force_mobile
        logging.debug("enforced mobileness to {0}".format(self.force_mobile))
