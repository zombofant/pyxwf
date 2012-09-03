import os, abc, logging

from PyXWF.utils import ET, _F
import PyXWF.utils as utils
import PyXWF.Nodes as Nodes
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Registry as Registry
import PyXWF.Errors as Errors
import PyXWF.Navigation as Navigation
import PyXWF.Document as Document
import PyXWF.Resource as Resource
import PyXWF.Namespaces as NS
import PyXWF.Types as Types
import PyXWF.Cache as Cache
import PyXWF.Sitleton as Sitleton

import PyXWF.Nodes.Directory as Directory

cacheLogging = logging.getLogger("PyXWF.Cache")

class TransformNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/nodes/transform"

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

        self._transforms = self.Site.templateCache
        self._xmlData = self.Site.xmlDataCache
        self._parser = self.Site.parserRegistry[ContentTypes.PyWebXML]

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

class TransformNode(TransformBase, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = str(TransformNS)
    names = ["node"]

    def __init__(self, site, parent, node):
        super(TransformNode, self).__init__(site, parent, node)
        self._navTitle = self._navTitleType(node.get("nav-title"))
        self._cache = TransformCacheSitleton.getCache(site)

    def _rebuild(self):
        transform = self._transforms[self._transformFile]
        source = self._xmlData[self._sourceFile]
        parser = self._parser
        docPage = transform.rawTransform(source.Tree, self._args).getroot()
        return parser.parseTree(docPage)

    def update(self):
        lastModified = self._calcLastModified()
        if lastModified > self._lastModified:
            self._transforms.update(self._transformFile)
            self._xmlData.update(self._sourceFile)
            self._cache.update(self)
            self._cache[self]

    def resolvePath(self, ctx, relPath):
        result = super(TransformNode, self).resolvePath(ctx, relPath)
        if result is self:
            ctx.useResource(self)
        return result

    def doGet(self, ctx):
        return self._cache[self]

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
        self._transform = self.Site.templateCache[self._transformFile]
        self._source = self.Site.xmlDataCache[self._sourceFile]

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

    def update(self):
        lastModified = self._calcLastModified()
        if lastModified > self._lastModified:
            self._transforms.update(self._transformFile)
            self._xmlData.update(self._sourceFile)
            self._rebuild()
            self._lastModified = lastModified


class TransformRoot(Directory.DirectoryBase):
    def __init__(self, tree, node):
        super(TransformRoot, self).__init__(tree.Site, tree, None)
        self._name = None
        self._path = tree.Path

        self._loadChildren(node)

class TransformCache(Cache.SubCache):
    def getLastModified(self, node):
        return node._calcLastModified()

    def update(self, node):
        with self._lookupLock:
            try:
                del self[node]
            except KeyError:
                pass

    def _load(self, node):
        return node._rebuild()

    def __getitem__(self, node):
        with self._lookupLock:
            try:
                return super(TransformCache, self).__getitem__(node)
            except KeyError:
                cacheLogging.debug(_F("MISS: {0} in {1}", node, self))
                obj = self._load(node)
                self[node] = obj
                return obj

    def __repr__(self):
        return "<TransformCache>"

class TransformCacheSitleton(Sitleton.Sitleton):
    __metaclass__ = Registry.SitletonMeta

    def __init__(self, site):
        super(TransformCacheSitleton, self).__init__(site)
        self.key = id(self)
        self.cache = site.cache.specializedCache(self.key, TransformCache)

    @classmethod
    def getCache(cls, site):
        return cls.atSite(site).cache
