import os

import PyWeb.Errors as Errors

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation

class RedirectBase(Nodes.Node):
    namespace = "http://pyweb.zombofant.net/xmlns/nodes/redirect"

    methods = {
        "found": Errors.Found,
        "see-other": Errors.SeeOther,
        "moved-permanently": Errors.MovedPermanently,
        "temporary-redirect": Errors.TemporaryRedirect,
        "internal": Errors.InternalRedirect
    }

    def __init__(self, site, parent, node):
        super(RedirectBase, self).__init__(site, parent, node)
        self.method = self.methods[node.get("method", "found")]
    
    def redirect(self, relPath):
        raise self.method(self.Target)

    def resolvePath(self, fullPath, relPath):
        if relPath != "":
            raise Errors.NotFound(resource=fullPath)
        if self.method is Errors.InternalRedirect:
            raise self.method(self.Target)
        else:
            return (self, relPath)
        
    requestHandlers = redirect

class RedirectInternal(RedirectBase):
    __metaclass__ = Registry.NodeMeta
    
    namespace = RedirectBase.namespace
    names = ["internal"]
    
    def __init__(self, site, parent, node):
        super(RedirectInternal, self).__init__(site, parent, node)
        self.to = node.get("to")
        
    @property
    def Target(self):
        if hasattr(self, "target"):
            return self.target
        else:
            self.target = self.site.getNode(self.to).Path
