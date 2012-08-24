from __future__ import unicode_literals

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Registry as Registry
import PyXWF.Crumbs as Crumbs
import PyXWF.Navigation as Navigation
import PyXWF.Types as Types

class Breadcrumbs(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    namespace = "http://pyxwf.zombofant.net/xmlns/crumbs/breadcrumbs"
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
        self.minDisplay = Types.Typecasts.int(node.get("min-display", 1))
        self.rich = self._richMap(node.get("rich"))
        self.rdfaPrefix = node.get("rdfa-prefix", "v:")

    def render(self, ctx, intoNode, atIndex):
        if not ctx.PageNode:
            return None
        ul = ET.Element(NS.XHTML.ul)
        hadNodes = set()
        pageNode = ctx.PageNode
        for node in pageNode.iterUpwards():
            if node is self.root:
                break
            navInfo = node.getNavigationInfo(ctx)
            display = navInfo.getDisplay()
            if ((display is Navigation.ReplaceWithChildren
                    or display < self.minDisplay)
                and (node is not pageNode or not self.forceShowCurrent)):
                continue

            representative = navInfo.getRepresentative()
            if representative in hadNodes:
                continue

            hadNodes.add(representative)
            li = ET.Element(NS.XHTML.li)
            relevant = li
            if node is not pageNode:
                a = ET.SubElement(li, NS.PyWebXML.a, href=representative.Path)
                a.text = navInfo.getTitle()
                relevant = a
                tail = False
            else:
                li.text = navInfo.getTitle()
                tail = True
            self.rich(self, ctx, relevant, isTail=tail)
            ul.insert(0, li)
        intoNode.insert(atIndex, ul)

    def rdfa(self, ctx, relevantNode, isTail=False):
        prefix = self.rdfaPrefix
        if not isTail:
            relevantNode.set("typeof", "v:Breadcrumb")
        else:
            relevantNode.set("typeof", "v:Breadcrumb")

    def schema(self, ctx, relevantNode, isTail=False):
        relevantNode.set("property", "breadcrumb")
        if isTail:
            relevantNode.set(NS.PyWebXML.content, ctx.PageNode.Path)

    def norich(self, *args, **kwargs):
        pass

    _richMap = Types.EnumMap({
        "rdfa": rdfa,
        "schema.org": schema,
        None: norich
    })
