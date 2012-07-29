import abc

import PyWeb.Errors as Errors
import PyWeb.Registry as Registry

class Node(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, tag, node, site):
        super(Node, self).__init__()
        self.site = site
        self.name = node.get("name")
    
    def nodeTree(self):
        yield self._nodeTreeEntry()

    @abc.abstractmethod
    def getDocument(self):
        return None

    def resolvePath(self, fullPath, relPath):
        if relPath == "":
            return self
        raise Errors.NotFound(resourceName=fullPath)

