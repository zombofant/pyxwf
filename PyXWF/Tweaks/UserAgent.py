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
    tweakNames = ["force-mobile"]

    def __init__(self, site):
        super(ForceMobile, self).__init__()
        site.hooks.register("handle.pre-lookup", self.forceMobile)
        self.Site = site
        self.forceMobile = Types.Typecasts.bool(self._tweaks["force-mobile"][-1].get("mobile"))

    def forceMobile(self, ctx):
        ctx.IsMobileClient = self.forceMobile
        logging.debug("enforced mobileness to {0}".format(self.forceMobile))
