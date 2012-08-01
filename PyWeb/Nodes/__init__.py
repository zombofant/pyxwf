import abc, collections

import PyWeb.utils as utils
import PyWeb.Errors as Errors

class NodeMeta(abc.ABCMeta):
    def _raiseNoValidRequestHandlers(mcls):
        raise TypeError("{0} requires requestHandlers as dict (or dict-compatible) or callable".format(name))
    
    def __new__(mcls, name, bases, dct):
        try:
            requestHandlers = dct["requestHandlers"]
        except KeyError:
            for base in bases:
                try:
                    requestHandlers = base.requestHandlers
                    break;
                except AttributeError:
                    pass
            else:
                mcls._raiseNoValidRequestHandlers(mcls)
        if requestHandlers is None:
            raise TypeError("requestHandlers has been set to None intentionally in {0}".format(name))

        isCallable = hasattr(requestHandlers, "__call__")
        if not isCallable:
            try:
                requestHandlers = dict(requestHandlers)
            except (ValueError, TypeError):
                try:
                    methods = dict(requestHandlers.items())
                except (ValueError, TypeError, AttributeError):
                    mcls._raiseNoValidRequestHandlers(mcls)
        else:
            requestHandlers = collections.defaultdict(lambda x: requestHandlers)
            

        for val in requestHandlers.viewvalues():
            if not hasattr(val, "__call__"):
                raise TypeError("All values in requestHandlers dict must be callable.")

        return abc.ABCMeta.__new__(mcls, name, bases, dct)

class Node(object):
    __metaclass__ = NodeMeta
    
    def __init__(self, site, parent, node):
        super(Node, self).__init__()
        self.parent = parent
        self.site = site
        if node is not None:
            self._id = node.get("id")
            self._name = node.get("name", "")
            self._template = node.get("template", None)
            parentPath = (parent.Path + "/") if parent is not None else ""
            self._path = parentPath + self._name
        else:
            self._id = None
            self._name = None
            self._template = None
            self._path = None
        
        if self.ID is not None:
            site.registerNodeID(self.ID, self)

    def iterUpwards(self, stopAt=None):
        node = self
        while node is not None and node is not stopAt:
            yield node
            node = node.parent
    
    def nodeTree(self):
        yield self._nodeTreeEntry()

    def handle(self, ctx):
        try:
            handler = self.requestHandlers[ctx.method]
        except KeyError:
            raise Errors.MethodNotAllowed(ctx.method)
        except TypeError:
            return self.requestHandlers(ctx)
        return handler(self, ctx)

    def resolvePath(self, fullPath, relPath):
        if relPath == "":
            return (self, relPath)
        raise Errors.NotFound(resourceName=fullPath)

    @property
    def Template(self):
        template = self._template
        if template is None and self.parent is not None:
            template = self.parent.Template
        return template
    
    @Template.setter
    def Template(self, value):
        self._template = value
        
    @property
    def Name(self):
        return self._name
        
    @property
    def Path(self):
        return self._path
            
    @property
    def ID(self):
        return self._id

    @abc.abstractmethod
    def getNavigationInfo(self, ctx):
        pass
    
    requestHandlers = {}


class DirectoryResolutionBehaviour(object):
    """
    Mixin to make a node behave like a directory, regarding the working of
    *resolvePath*. For this, the method *_getChildNode* must be implemented.

    If the path points to the node using this behaviour and is missing a
    trailing /, a redirect is issued. Otherwise, the next path segment is taken
    (i.e. the part *behind* the / which follows the path to the current node but
    *in front of* the next /, if any) and a lookup using *_getChildNode* is
    attempted.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _getChildNode(self, key):
        """
        Return the node at the path segment *key*. *key* will be the empty
        string, if no next path segment is given in the path.

        Returns ``None`` if there is no Node at the given *key*.

        Raise a HTTPRedirect error if the resource can be found under a
        different location. Set *local* attribute of that exception to any value
        and pass only the new key to *newLocation* to automatically generate
        correct paths.
        """

    def resolvePath(self, fullPath, relPath):
        if fullPath[-1:] != "/" and len(relPath) == 0 and len(fullPath) > 0:
            raise Errors.Found(newLocation=fullPath+"/")
        try:
            pathHere, relPath = relPath.split("/", 1)
        except ValueError:
            pathHere = relPath
            relPath = ""
        try:
            node = self._getChildNode(pathHere)
        except Errors.HTTPRedirection as err:
            if hasattr(err, "local"):
                trailPathLen = len(relPath)+len(pathHere)+1
                newLocation = fullPath[:-(trailPathLen)] + err.newLocation + relPath
            else:
                raise
        if node is None:
            raise Errors.NotFound()
        if node is not self:
            return node.resolvePath(fullPath, relPath)
        else:
            return node, relPath
