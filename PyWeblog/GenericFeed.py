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

        def doGet(self, ctx):
            return self.feed.doGet(ctx, self.node)

        def getContentType(self, ctx):
            return self.feed.ContentType

        def getNavigationInfo(self, ctx):
            assert False

        requestHandlers = {
            "GET": doGet
        }

    def __init__(self, site, parent, node):
        if not isinstance(parent, Protocols.Feeds):
            raise BadParent(node, parent)
        super(GenericFeed, self).__init__()
        self.Site = site
        self.Blog = parent.Blog
        self._limit = Types.NumericRange(int, 1, None)(node.get("limit", 10))
        self._linkPrefix = Types.NotNone(node.get("link-prefix"))
        self._idPrefix = node.get("id-prefix", self._linkPrefix)
        self._iconHref = node.get("icon-href")
        self._rootID = node.get("root-id")
        self._mapUpdatedToLastModified = Types.Typecasts.bool(node.get("map-updated-to-last-modified", True))

    @abc.abstractproperty
    def ContentType(self):
        """
        Return the MIME type of the feed.
        """

    @property
    def QueryValue(self):
        return self._queryValue

    def doGet(self, ctx, node):
        root = ET.Element(NS.PyBlog.syndication, attrib={
            "kind": node.SelectionCriterion,
            "title": node.SelectionValue
        })
        rootID = ET.SubElement(root, NS.PyBlog.id).text = \
            self._rootID or (self._idPrefix + self.Blog.Path)
        if self._mapUpdatedToLastModified:
            updatedKey = operator.attrgetter("LastModified")
        else:
            updatedKey = operator.attrgetter("creationDate")

        posts = list(itertools.islice(node.getPosts(), 0, self._limit))
        if len(posts) > 0:
            ET.SubElement(root, getattr(NS.PyBlog, "updated")).text = \
                max(map(updatedKey, posts)).isoformat() + "Z"
        ET.SubElement(root, getattr(NS.PyBlog, "feed-path")).text = ctx.FullURI
        ET.SubElement(root, getattr(NS.PyBlog, "node-path")).text = node.Path
        ET.SubElement(root, getattr(NS.PyBlog, "blog-path")).text = self.Blog.Path
        for post in posts:
            postNode = ET.SubElement(root, NS.PyBlog.post)
            ET.SubElement(postNode, NS.PyBlog.id).text = self._idPrefix + post.path
            ET.SubElement(postNode, NS.PyBlog.updated).text = updatedKey(post).isoformat() + "Z"
            postNode.append(post.getPyWebXML())

        return self.transform(ctx, root)

    def getFeedNode(self):
        el = ET.Element(NS.PyBlog.feed, attrib={
            "query-value": self.QueryValue,
            "name": "Atom",
            "type": self.ContentType
        })
        if self._iconHref:
            el.set("img-href", self._iconHref)
        return el

    def proxy(self, ctx, node):
        ctx.useResource(self.Site.templateCache[self._template])
        return self.Proxy(self, node)

    def transform(self, ctx, root):
        self.Site.transformReferences(ctx, root)
        feed = self.Site.templateCache[self._template].rawTransform(root, {})
        self.Site.transformPyNamespace(ctx, feed, crumbs=False, link=False)
        return feed
