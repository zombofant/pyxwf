from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Registry as Registry
import PyWeb.Crumbs as Crumbs
import PyWeb.Navigation as Navigation
import PyWeb.Types as Types

class Breadcrumbs(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    namespace = "http://pyweb.zombofant.net/xmlns/crumbs/breadcrumbs"
    names = ["crumb"]

    def __init__(self, site, node):
        super(Breadcrumbs, self).__init__(site, node)
        rootID = node.get("root")
        if rootID is not None:
            self.root = site.getNode(rootID)
        else:
            self.root = None
        self.forceShowCurrent = Types.Typecasts.bool(
            node.get("force-show-current", False))

    def render(self, ctx):
        ul = ET.Element(NS.XHTML.ul)
        hadNodes = set()
        pageNode = ctx.PageNode
        for node in pageNode.iterUpwards():
            if node is self.root:
                break
            navInfo = node.getNavigationInfo(ctx)
            if navInfo.getDisplay() != Navigation.Show and (
                    node is not pageNode or not self.forceShowCurrent):
                continue

            representative = navInfo.getRepresentative()
            if representative in hadNodes:
                continue
            
            hadNodes.add(representative)
            li = ET.Element(NS.XHTML.li)
            if node is not pageNode:
                a = ET.SubElement(li, NS.PyWebXML.a, href=representative.Path)
                a.text = navInfo.getTitle()
            else:
                li.text = navInfo.getTitle()
            ul.insert(0, li)
        return ul
