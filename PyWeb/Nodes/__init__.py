import abc

import PyWeb.Errors as Errors

class Node(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, title, urlName, navName):
        super(Node, self).__init__()
        self.title = title
        self.urlName = urlName
        self.navName = navName

    @abc.abstractmethod
    def _nodeTreeEntry(self):
        pass
    
    def nodeTree(self):
        yield self._nodeTreeEntry()

    def getDocument(self, path):
        if path != "":
            raise Errors.NotFound()

class ContainerNode(Node, list):
    def nodeTree(self):
        for item in super(ContainerNode, self).nodeTree():
            yield item
        for child in self:
            for entry in child.nodeTree():
                yield "    "+entry
