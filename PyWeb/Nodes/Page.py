import os

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation
import PyWeb.Document as Document
import PyWeb.Resource as Resource

class Page(Nodes.Node, Navigation.Info, Resource.Resource):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/page"
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Page, self).__init__(site, parent, node)

        self.navTitle = self._navTitleWithNoneType(node.get("nav-title"))
        self.navDisplay = Navigation.DisplayMode(node.get("nav-display"),
            default=Navigation.Show)
        self.mimeType = node.get("type")
        self.fileName = os.path.join(site.root, node.get("src"))
        self._lastModified = None
        self.title = None

    @property
    def LastModified(self):
        return self._lastModified

    def update(self):
        docRef = self._getDocRef()
        if self._lastModified is None or \
                self._lastModified < docRef.LastModified:

            self._lastModified = docRef.LastModified
            self.title = self.navTitle or docRef.doc.title

    def _getDocRef(self):
        return self.site.fileDocumentCache.get(self.fileName, self.mimeType)

    def doGet(self, ctx):
        return self._getDocRef().doc

    def resolvePath(self, ctx, relPath):
        result = super(Page, self).resolvePath(ctx, relPath)
        ctx.useResource(self)
        return result

    def getTitle(self):
        return self.title

    def getDisplay(self):
        return self.navDisplay

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        if self.title is None:
            self.update()
        return self

    requestHandlers = {
        "GET": doGet
    }
