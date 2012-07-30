from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Registry as Registry
import PyWeb.Crumbs as Crumbs
import PyWeb.Navigation as Nav

class IteratorStack(object):
    def __init__(self):
        self.stack = []
        self.curr = None

    def push(self, new):
        if self.curr is not None:
            self.stack.append(self.curr)
            self.curr = new
        else:
            self.curr = new

    def next(self):
        try:
            return next(self.curr)
        except StopIteration:
            try:
                self.curr = self.stack.pop()
                return next(self)
            except IndexError:
                raise StopIteration()

    def __iter__(self):
        return self

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
        self.childActiveClass = node.get("child-active-class")

    def _propagateActive(self, eNode):
        cls = self.activeClass
        while eNode is not None:
            if eNode.tag == NS.XHTML.li:
                utils.addClass(eNode, cls)
            if not self.childActiveClass:
                return
            eNode = eNode.getparent()
            cls = self.childActiveClass
    
    def _navTree(self, parent, ctx, info, depth=0):
        if self.maxDepth > 0 and depth > self.maxDepth:
            return
        nodeIterable = IteratorStack()
        try:
            nodeIterable.push(iter(info))
        except (ValueError, TypeError):
            return
        if parent is not None:
            ul = ET.SubElement(parent, NS.XHTML.ul)
        else:
            ul = ET.Element(NS.XHTML.ul)
        
        for child in nodeIterable:
            navInfo = child.getNavigationInfo(ctx)
            displayMode = navInfo.getDisplay()
            if displayMode is Nav.ReplaceWithChildren:
                nodeIterable.push(iter(navInfo))
            elif displayMode is Nav.Show:
                li = ET.SubElement(ul, NS.XHTML.li)
                a = ET.SubElement(li, NS.PyWebXML.a, href=child.Path)
                a.text = navInfo.getTitle()
                subtree = self._navTree(li, ctx, navInfo, depth+1)
                if navInfo.getRepresentative() is ctx.pageNode:
                    self._propagateActive(li)
                if subtree is not None:
                    li.append(subtree)
        return ul

    def render(self, ctx):
        if self.showRoot:
            return self._navTree(None, ctx, [self.root], depth=0)
        else:
            return self._navTree(None, ctx, self.root.getNavigationInfo(ctx))
