import PyWeb.Errors as Errors

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry

class Redirect(Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/redirect"

    def __init__(self, tag, node, site):
        super(Redirect, self).__init__(tag, node, site)
        if tag != "node":
            raise ValueError("Unknown node name: {0}".format(name))
        self.target = node.get("to")
    
    def getDocument(self):
        pass

    def resolvePath(self, fullPath, relPath):
        raise Found(os.path.join(fullPath[:-(len(relPath)+len(self.name)+1)], self.target, relPath))

    def _nodeTreeEntry(self):
        return """<Page title="{0}">""".format(self.doc.title)
