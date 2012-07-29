import abc

import PyWeb.Errors as Errors
import PyWeb.Registry as Registry

class Node(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, parent, tag, node, site):
        super(Node, self).__init__()
        self.parent = parent
        self.site = site
        self.name = node.get("name")
        self.template = node.get("template", None)
    
    def nodeTree(self):
        yield self._nodeTreeEntry()

    @abc.abstractmethod
    def getDocument(self):
        return None

    def resolvePath(self, fullPath, relPath):
        if relPath == "":
            return self
        raise Errors.NotFound(resourceName=fullPath)

    def getTemplate(self):
        template = self.template
        if template is None and self.parent is not None:
            template = self.parent.getTemplate()
        return template
