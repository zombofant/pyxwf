import os

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation
import PyWeb.Document as Document

class Page(Nodes.Node, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/page"
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Page, self).__init__(site, parent, node)

        self.src = node.get("src")
        self.navTitle = self._navTitleWithNoneType(node.get("nav-title"))
        self.navDisplay = Navigation.DisplayMode(node.get("nav-display"),
            default=Navigation.Show)
        self.mimeType = node.get("type")

        fileName = os.path.join(site.root, self.src)
        self.docRef = Document.FileDocument(fileName,
            overrideMIME=self.mimeType)
    
    def doGet(self, ctx):
        return self.docRef.doc

    def resolvePath(self, ctx, relPath):
        result = super(Page, self).resolvePath(ctx, relPath)
        ctx.useResource(self.docRef)
        return result

    def getTitle(self):
        return self.navTitle or self.docRef.doc.title

    def getDisplay(self):
        return self.navDisplay

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        return self
        
    requestHandlers = {
        "GET": doGet
    }
