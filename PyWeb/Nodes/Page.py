import os

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry

class Page(Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/page"
    names = ["node"]

    def __init__(self, parent, tag, node, site):
        super(Page, self).__init__(parent, tag, node, site)
        if tag != "node":
            raise ValueError("Unknown node name: {0}".format(name))

        self.src = node.get("src")
        self.mimeType = node.get("type")

        documentHandler = Registry.DocumentPlugins.getPluginInstance(self.mimeType)
        f = open(os.path.join(site.root, self.src), "r")
        try:
            self.doc = documentHandler.parse(f)
        finally:
            f.close()
    
    def doGet(self, relPath):
        return self.doc

    def _nodeTreeEntry(self):
        return """<Page title="{0}">""".format(self.doc.title)
        
    requestHandlers = {
        "GET": doGet
    }
