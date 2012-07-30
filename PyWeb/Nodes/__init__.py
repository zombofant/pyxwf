import abc, collections

import PyWeb.Errors as Errors

class NodeMeta(abc.ABCMeta):
    def __new__(mcls, name, bases, dct):
        requestHandlers = dct.get("requestHandlers", None)

        isCallable = hasattr(requestHandlers, "__call__")
        if not isCallable:
            try:
                requestHandlers = dict(requestHandlers)
            except ValueError, TypeError:
                try:
                    methods = dict(requestHandlers.items())
                except ValueError, TypeError:
                    raise TypeError("Node requires requestHandlers as dict (or dict-compatible) or callable")
        else:
            requestHandlers = collections.defaultdict(lambda x: requestHandlers)
            

        for val in requestHandlers.viewvalues():
            if not hasattr(val, "__call__"):
                raise TypeError("All values in requestHandlers dict must be callable.")

        return abc.ABCMeta.__new__(mcls, name, bases, dct)

class Node(object):
    __metaclass__ = NodeMeta
    
    def __init__(self, parent, tag, node, site):
        super(Node, self).__init__()
        self.parent = parent
        self.site = site
        self.name = node.get("name")
        self.template = node.get("template", None)
    
    def nodeTree(self):
        yield self._nodeTreeEntry()

    def handle(self, request, relPath):
        try:
            handler = self.requestHandlers[request.method]
        except KeyError:
            raise Errors.MethodNotAllowed(request.method)
        return handler(self, relPath)

    def resolvePath(self, fullPath, relPath):
        if relPath == "":
            return (self, relPath)
        raise Errors.NotFound(resourceName=fullPath)

    def getTemplate(self):
        template = self.template
        if template is None and self.parent is not None:
            template = self.parent.getTemplate()
        return template
    
    requestHandlers = {}
