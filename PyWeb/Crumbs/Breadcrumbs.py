from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Registry as Registry
import PyWeb.Crumbs as Crumbs
import PyWeb.Navigation as Nav

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

    def render(self, ctx):
        ul = ET.Element(NS.XHTML.ul)
        node = ctx.pageNode
        hadNodes = set()
        while node is not self.root and node is not None:
            navInfo = node.getNavigationInfo(ctx)
            if navInfo.getDisplay() == Nav.Show:
                representative = navInfo.getRepresentative()
                if not representative in hadNodes:
                    hadNodes.add(representative)
                    li = ET.Element(NS.XHTML.li)
                    if node is not ctx.pageNode:
                        a = ET.SubElement(li, NS.PyWebXML.a, href=representative.Path)
                        a.text = navInfo.getTitle()
                    else:
                        li.text = navInfo.getTitle()
                    ul.insert(0, li)
            node = node.parent
        return ul
