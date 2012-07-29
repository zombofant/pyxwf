import os

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry

class Page(Nodes.ContainerNode):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.sotecware.net/page"

    def __init__(self, name, node, site):
        if name != "node":
            raise ValueError("Unknown node name: {0}".format(name))

        self.src = node.get("src")
        self.mimeType = node.get("type")

        documentHandler = Registry.DocumentPlugins.getPluginInstance(self.mimeType)
        f = open(os.path.join(site.root, self.src), "r")
        try:
            self.doc = documentHandler.parse(f)
        finally:
            f.close()
    
    def _render(self, path):
        return self.doc

    def _nodeTreeEntry(self):
        return """<Page title="{0}">""".format(self.doc.title)
