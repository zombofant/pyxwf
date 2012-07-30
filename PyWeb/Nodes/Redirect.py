import os

import PyWeb.Errors as Errors

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry

class Redirect(Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/redirect"
    names = ["node"]

    methods = {
        "found": Errors.Found,
        "see-other": Errors.SeeOther,
        "moved-permanently": Errors.MovedPermanently,
        "temporary-redirect": Errors.TemporaryRedirect,
        "internal": Errors.InternalRedirect
    }

    def __init__(self, parent, tag, node, site):
        super(Redirect, self).__init__(parent, tag, node, site)
        if tag != "node":
            raise ValueError("Unknown node name: {0}".format(name))
        self.target = node.get("to")
        self.method = self.methods[node.get("method", "found")]
    
    def redirect(self, relPath):
        newPath = os.path.join(fullPath[:-(len(relPath)+len(self.name)+1)])
        newPath = os.path.join(newPath, self.target, relPath)
        raise self.method(newPath)

    def resolvePath(self, fullPath, relPath):
        if self.method is Errors.InternalRedirect:
            newPath = os.path.join(fullPath[:-(len(relPath)+len(self.name)+1)])
            newPath = os.path.join(newPath, self.target, relPath)
            raise self.method(newPath)
        else:
            return (self, relPath)

    def _nodeTreeEntry(self):
        return """<Page title="{0}">""".format(self.doc.title)
        
    requestHandlers = redirect
