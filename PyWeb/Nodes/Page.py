import os

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation

class Page(Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/page"
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Page, self).__init__(site, parent, node)

        self.src = node.get("src")
        self.mimeType = node.get("type")

        documentHandler = Registry.DocumentPlugins(self.mimeType)
        f = open(os.path.join(site.root, self.src), "r")
        try:
            self.doc = documentHandler.parse(f)
        finally:
            f.close()
        
        self._navigationTitle = self.doc.title
    
    def doGet(self, relPath):
        return self.doc

    def _nodeTreeEntry(self):
        return """<Page title="{0}">""".format(self.doc.title)
        
    requestHandlers = {
        "GET": doGet
    }
