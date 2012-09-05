from __future__ import unicode_literals, absolute_import, print_function

import abc, operator, itertools

from PyXWF.utils import ET, _F
import PyXWF.Nodes as Nodes
import PyXWF.Namespaces as NS
import PyXWF.Types as Types

import PyWeblog.Protocols as Protocols

class GenericFeed(Protocols.Feed):
    __metaclass__ = abc.ABCMeta

    class Proxy(Nodes.Node):
        __metaclass__ = Nodes.NodeMeta

        def __init__(self, feed, node):
            self.feed = feed
            self.node = node

        @property
        def Template(self):
            return self.node.Template

        def do_GET(self, ctx):
            return self.feed.do_GET(ctx, self.node)

        def get_content_type(self, ctx):
            return self.feed.ContentType

        def get_navigation_info(self, ctx):
            assert False

        request_handlers = {
            "GET": do_GET
        }

    def __init__(self, site, parent, node):
        if not isinstance(parent, Protocols.Feeds):
            raise BadParent(node, parent)
        super(GenericFeed, self).__init__()
        self.Site = site
        self.Blog = parent.Blog
        self._limit = Types.NumericRange(int, 1, None)(node.get("limit", 10))
        self._link_prefix = Types.NotNone(node.get("link-prefix"))
        self._idprefix = node.get("id-prefix", self._link_prefix)
        self._iconhref = node.get("icon-href")
        self._rootid = node.get("root-id")
        self._map_updated_to_last_modified = Types.Typecasts.bool(node.get("map-updated-to-last-modified", True))

    @abc.abstractproperty
    def ContentType(self):
        """
        Return the MIME type of the feed.
        """

    @property
    def QueryValue(self):
        return self._query_value

    def do_GET(self, ctx, node):
        root = ET.Element(NS.PyBlog.syndication, attrib={
            "kind": node.SelectionCriterion,
            "title": node.SelectionValue
        })
        rootid = ET.SubElement(root, NS.PyBlog.id).text = \
            self._rootid or (self._idprefix + node.Path)
        if self._map_updated_to_last_modified:
            updated_key = operator.attrgetter("LastModified")
        else:
            updated_key = operator.attrgetter("creation_date")

        posts = list(itertools.islice(node.get_posts(), 0, self._limit))
        if len(posts) > 0:
            ET.SubElement(root, getattr(NS.PyBlog, "updated")).text = \
                max(map(updated_key, posts)).isoformat() + "Z"
        ET.SubElement(root, getattr(NS.PyBlog, "feed-path")).text = ctx.FullURI
        ET.SubElement(root, getattr(NS.PyBlog, "node-path")).text = node.Path
        ET.SubElement(root, getattr(NS.PyBlog, "blog-path")).text = self.Blog.Path
        for post in posts:
            postnode = ET.SubElement(root, NS.PyBlog.post)
            ET.SubElement(postnode, NS.PyBlog.id).text = self._idprefix + post.path
            ET.SubElement(postnode, NS.PyBlog.updated).text = updated_key(post).isoformat() + "Z"
            postnode.append(post.get_PyWebXML())

        return self.transform(ctx, root)

    def get_feed_node(self):
        el = ET.Element(NS.PyBlog.feed, attrib={
            "query-value": self.QueryValue,
            "name": "Atom",
            "type": self.ContentType
        })
        if self._iconhref:
            el.set("img-href", self._iconhref)
        return el

    def proxy(self, ctx, node):
        ctx.use_resource(self.Site.template_cache[self._template])
        return self.Proxy(self, node)

    def transform(self, ctx, root):
        self.Site.transform_references(ctx, root)
        feed = self.Site.template_cache[self._template].raw_transform(root, {})
        self.Site.transform_py_namespace(ctx, feed, crumbs=False, link=False)
        return feed
