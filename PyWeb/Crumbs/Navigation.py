from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Registry as Registry
import PyWeb.Crumbs as Crumbs

class Navigation(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    
    namespace = "http://pyweb.zombofant.net/xmlns/crumbs/navigation"
    names = ["crumb"]

    def __init__(self, site, node):
        super(Navigation, self).__init__(site, node)
        self.root = site.getNode(node.get("root"))
        self.showRoot = utils.getBoolAttr(node, "show-root", False)
        self.maxDepth = int(node.get("max-depth", 0))
        self.activeClass = node.get("active-class", "nav-active")
        self.propagateActive = utils.getBoolAttr(node, "propagate-active", True)
    
    def _navTree(self, node, mainNode, depth=0):
        return ET.Element(NS.XHTML.span)

    def render(self, mainNode):
        if self.showRoot:
            return self._navTree([self.root], mainNode, depth=0)
        else:
            return self._navTree(self.root, mainNode)
