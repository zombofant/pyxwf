from PyWeb.utils import ET
import PyWeb.Namespaces as NS
import PyWeb.Registry as Registry
import PyWeb.Crumbs as Crumbs

class Navigation(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    
    namespace = "http://pyweb.zombofant.net/xmlns/crumbs/navigation"
    names = ["crumb"]

    def __init__(self, site, node):
        super(Navigation, self).__init__(site, node)

    def render(self, mainNode):
        span = ET.Element(NS.XHTML.span)
        span.text = "I am not a navigation, I just pretend to be."
        return span
