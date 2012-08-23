import os, abc

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Nodes as Nodes
import PyWeb.ContentTypes as ContentTypes
import PyWeb.Registry as Registry
import PyWeb.Errors as Errors
import PyWeb.Navigation as Navigation
import PyWeb.Document as Document
import PyWeb.Resource as Resource
import PyWeb.Namespaces as NS
import PyWeb.Types as Types

import PyWeb.Nodes.Directory as Directory

class TransformNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/nodes/transform"

class TransformBase(Nodes.Node, Resource.Resource):
    __metaclass__ = abc.ABCMeta

    _navTitleType = Types.NotNone
    _fileType = Types.NotNone
    _argName = Types.NotNone
    _argValue = Types.NotNone

    def __init__(self, site, parent, node):
        super(TransformBase, self).__init__(site, parent, node)
        self._transformFile = self._fileType(node.get("transform"))
        self._sourceFile = self._fileType(node.get("src"))

        self._args = dict(
                (self._argName(argNode.get("name")),
                    utils.unicodeToXPathStr(self._argValue(argNode.get("value"))))
            for argNode in node.findall(TransformNS.arg))

        self._transforms = self.site.templateCache
        self._xmlData = self.site.xmlDataCache
        self._parser = self.site.parserRegistry[ContentTypes.PyWebXML]

        self._lastModified = self._calcLastModified()
        self._rebuild()

    def _calcLastModified(self):
        lastModified = self._transforms.getLastModified(self._transformFile)
        if lastModified is None:
            raise Errors.ResourceLost(self._transformFile)
        try:
            return max(
                lastModified,
                self._xmlData.getLastModified(self._sourceFile)
            )
        except TypeError:
            raise Errors.ResourceLost(self._sourceFile)

    @property
    def LastModified(self):
        return self._lastModified

    def update(self):
        lastModified = self._calcLastModified()
        if lastModified > self._lastModified:
            self._transforms.update(self._transformFile)
            self._xmlData.update(self._sourceFile)
            self._rebuild()
            self._lastModified = lastModified

class TransformNode(TransformBase, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = str(TransformNS)
    names = ["node"]

    def __init__(self, site, parent, node):
        super(TransformNode, self).__init__(site, parent, node)
        self._navTitle = self._navTitleType(node.get("nav-title"))

    def _rebuild(self):
        transform = self._transforms[self._transformFile]
        source = self._xmlData[self._sourceFile]
        parser = self._parser
        docPage = transform.rawTransform(source.Tree, self._args).getroot()
        self._doc = parser.parseTree(docPage)

    def resolvePath(self, ctx, relPath):
        result = super(TransformNode, self).resolvePath(ctx, relPath)
        if result is self:
            ctx.useResource(self)
        return result

    def doGet(self, ctx):
        return self._doc

    def getTitle(self):
        return self._navTitle

    def getNavigationInfo(self, ctx):
        return self

    def getDisplay(self):
        return Navigation.Show

    def getRepresentative(self):
        return self

    requestHandlers = {
        "GET": doGet
    }

class TransformTree(TransformBase):
    __metaclass__ = Registry.NodeMeta

    namespace = str(TransformNS)
    names = ["tree"]

    def _rebuild(self):
        self._transform = self.site.templateCache[self._transformFile]
        self._source = self.site.xmlDataCache[self._sourceFile]

        tree = self._transform.rawTransform(self._source.Tree, self._args)

        root = tree.getroot()
        if root.tag != TransformNS.root:
            raise ValueError("Result of transform:tree transformation must have a transform:root node as root.")

        self._tree = TransformRoot(self, root)

    def resolvePath(self, ctx, relPath):
        ctx.useResource(self)
        return self._tree.resolvePath(ctx, relPath)

    def getNavigationInfo(self, ctx):
        ctx.useResource(self)
        return self._tree.getNavigationInfo(ctx)


class TransformRoot(Directory.DirectoryBase):
    def __init__(self, tree, node):
        super(TransformRoot, self).__init__(tree.site, tree, None)
        self._name = None
        self._path = tree.Path

        self._loadChildren(node)
