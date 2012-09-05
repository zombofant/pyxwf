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

cache_logging = logging.getLogger("PyXWF.Cache")

class TransformNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/nodes/transform"

class TransformBase(Nodes.Node, Resource.Resource):
    __metaclass__ = abc.ABCMeta

    _navtitle_type = Types.NotNone
    _file_type = Types.NotNone
    _arg_name = Types.NotNone
    _arg_value = Types.NotNone

    def __init__(self, site, parent, node):
        super(TransformBase, self).__init__(site, parent, node)
        self._transform_file = self._file_type(node.get("transform"))
        self._source_file = self._file_type(node.get("src"))

        self._args = dict(
                (self._arg_name(argnode.get("name")),
                    utils.unicode2xpathstr(self._arg_value(argnode.get("value"))))
            for argnode in node.findall(TransformNS.arg))

        self._transforms = self.Site.template_cache
        self._xmldata = self.Site.xml_data_cache
        self._parser = self.Site.parser_registry[ContentTypes.PyWebXML]

        self._last_modified = self._calc_last_modified()
        self._rebuild()

    def _calc_last_modified(self):
        last_modified = self._transforms.get_last_modified(self._transform_file)
        if last_modified is None:
            raise Errors.ResourceLost(self._transform_file)
        try:
            return max(
                last_modified,
                self._xmldata.get_last_modified(self._source_file)
            )
        except TypeError:
            raise Errors.ResourceLost(self._source_file)

    @property
    def LastModified(self):
        return self._last_modified

class TransformNode(TransformBase, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = str(TransformNS)
    names = ["node"]

    def __init__(self, site, parent, node):
        super(TransformNode, self).__init__(site, parent, node)
        self._navtitle = self._navtitle_type(node.get("nav-title"))
        self._cache = TransformCacheSitleton.get_cache(site)

    def _rebuild(self):
        transform = self._transforms[self._transform_file]
        source = self._xmldata[self._source_file]
        parser = self._parser
        docpage = transform.raw_transform(source.Tree, self._args).getroot()
        return parser.parse_tree(docpage)

    def update(self):
        last_modified = self._calc_last_modified()
        if last_modified > self._last_modified:
            self._transforms.update(self._transform_file)
            self._xmldata.update(self._source_file)
            self._cache.update(self)
            self._cache[self]

    def resolve_path(self, ctx, relpath):
        result = super(TransformNode, self).resolve_path(ctx, relpath)
        if result is self:
            ctx.use_resource(self)
        return result

    def do_GET(self, ctx):
        return self._cache[self]

    def get_title(self):
        return self._navtitle

    def get_navigation_info(self, ctx):
        return self

    def get_display(self):
        return Navigation.Show

    def get_representative(self):
        return self

    request_handlers = {
        "GET": do_GET
    }

class TransformTree(TransformBase):
    __metaclass__ = Registry.NodeMeta

    namespace = str(TransformNS)
    names = ["tree"]

    def _rebuild(self):
        self._transform = self.Site.template_cache[self._transform_file]
        self._source = self.Site.xml_data_cache[self._source_file]

        tree = self._transform.raw_transform(self._source.Tree, self._args)

        root = tree.getroot()
        if root.tag != TransformNS.root:
            raise ValueError("Result of transform:tree transformation must have a transform:root node as root.")

        self._tree = TransformRoot(self, root)

    def resolve_path(self, ctx, relpath):
        ctx.use_resource(self)
        return self._tree.resolve_path(ctx, relpath)

    def get_navigation_info(self, ctx):
        ctx.use_resource(self)
        return self._tree.get_navigation_info(ctx)

    def update(self):
        last_modified = self._calc_last_modified()
        if last_modified > self._last_modified:
            self._transforms.update(self._transform_file)
            self._xmldata.update(self._source_file)
            self._rebuild()
            self._last_modified = last_modified


class TransformRoot(Directory.DirectoryBase):
    def __init__(self, tree, node):
        super(TransformRoot, self).__init__(tree.Site, tree, None)
        self._name = None
        self._path = tree.Path

        self._load_children(node)

class TransformCache(Cache.SubCache):
    def get_last_modified(self, node):
        return node._calc_last_modified()

    def update(self, node):
        with self._lookuplock:
            try:
                del self[node]
            except KeyError:
                pass

    def _load(self, node):
        return node._rebuild()

    def __getitem__(self, node):
        with self._lookuplock:
            try:
                return super(TransformCache, self).__getitem__(node)
            except KeyError:
                cache_logging.debug(_F("MISS: {0} in {1}", node, self))
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
        self.cache = site.cache.specialized_cache(self.key, TransformCache)

    @classmethod
    def get_cache(cls, site):
        return cls.at_site(site).cache
