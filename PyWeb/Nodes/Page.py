import os

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation

class Page(Nodes.Node, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/page"
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Page, self).__init__(site, parent, node)

        self.src = node.get("src")
        self.navDisplay = Navigation.DisplayMode(node.get("nav-display"),
            default=Navigation.Show)
        self.mimeType = node.get("type")

        documentHandler = Registry.DocumentPlugins(self.mimeType)
        f = open(os.path.join(site.root, self.src), "r")
        try:
            self.doc = documentHandler.parse(f)
        finally:
            f.close()
    
    def doGet(self, ctx):
        ctx.checkNotModified(self.doc.lastModified)
        return self.doc

    def _nodeTreeEntry(self):
        return """<Page title="{0}">""".format(self.doc.title)

    def getTitle(self):
        return self.doc.title

    def getDisplay(self):
        return self.navDisplay

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        return self
        
    requestHandlers = {
        "GET": doGet
    }
