from __future__ import unicode_literals

import operator

from PyXWF.utils import ET
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Types as Types
import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation
import PyXWF.Namespaces as NS

class AtomFeedRoot(object):
    def __init__(self, cfgNode, blog):
        super(AtomFeedRoot, self).__init__()
        self.blog = blog
        self.Site = blog.Site

        self.templateName = Types.NotNone(cfgNode.get("template"))
        self.rootId = cfgNode.get("root-id")
        self.mapUpdatedToLastModified = Types.DefaultForNone(False,
            Types.Typecasts.bool)(cfgNode.get("map-updated-to-last-modified"))
        self.linkPrefix = Types.NotNone(cfgNode.get("link-prefix"))
        self.idPrefix = cfgNode.get("id-prefix", self.linkPrefix)
        self.limit = Types.NumericRange(Types.Typecasts.int, 1, None)(cfgNode.get("limit"))

    @staticmethod
    def Link(href, title=""):
        return ET.Element(NS.XHTML.link, attrib={
            "rel": "alternate",
            "type": ContentTypes.Atom,
            "href": href,
            "title": title
        })

    def prepare(self, ctx, posts):
        ctx.useResources(posts)
        self.template = self.Site.templateCache[self.templateName]
        ctx.useResource(self.template)

    def render(self, ctx, posts, title, kind, path):
        root = ET.Element(NS.PyBlog.syndication)
        root.set("title", title)
        root.set("kind", kind)
        rootID = ET.SubElement(root, NS.PyBlog.id)
        rootID.text = self.rootId or (self.idPrefix + self.blog.Path)
        if self.mapUpdatedToLastModified:
            updatedKey = operator.attrgetter("LastModified")
        else:
            updatedKey = operator.attrgetter("creationDate")

        rootUpdated = ET.SubElement(root, NS.PyBlog.updated)
        rootUpdated.text = max(map(updatedKey, posts)).isoformat() + "Z"
        rootPath = ET.SubElement(root, getattr(NS.PyBlog, "feed-path"))
        rootPath.text = ctx.FullURI
        rootNode = ET.SubElement(root, getattr(NS.PyBlog, "node-path"))
        rootNode.text = path
        rootBlog = ET.SubElement(root, getattr(NS.PyBlog, "blog-path"))
        rootBlog.text = self.blog.Path
        for post in posts:
            postNode = ET.SubElement(root, NS.PyBlog.post)
            postID = ET.SubElement(postNode, NS.PyBlog.id)
            postID.text = self.idPrefix + post.Path
            postUpdated = ET.SubElement(postNode, NS.PyBlog.updated)
            postUpdated.text = updatedKey(post).isoformat() + "Z"
            postNode.append(post.getArticle())

        self.Site.transformReferences(ctx, root)
        feed = self.template.rawTransform(root, {})
        self.Site.transformPyNamespace(ctx, feed, crumbs=False, link=False)
        for localLink in feed.iter(NS.PyWebXML.link):
            localLink.tag = NS.Atom.link
            self.Site.transformHref(ctx, localLink)
            localLink.text = self.linkPrefix[:-1]+localLink.get("href")
            del localLink.attrib["href"]
        return feed

class AtomFeedNode(Nodes.Node):
    def __init__(self, blogDir, title, kind):
        super(AtomFeedNode, self).__init__(blogDir.Site, blogDir, None)
        self.directory = blogDir
        self.title = title
        self.kind = kind

    def resolvePath(self, ctx, relPath):
        self.feedRoot = self.directory.blog.atomFeed
        if self.feedRoot is None:
            raise Errors.NotFound()
        result = super(AtomFeedNode, self).resolvePath(ctx, relPath)
        if result is self:
            self.posts = self.directory.getPosts()
            self.feedRoot.prepare(ctx, self.posts)
        return result

    def getContentType(self, ctx):
        return ContentTypes.Atom

    def handle(self, ctx):
        return self.feedRoot.render(ctx, self.posts, self.title, self.kind,
                self.directory.Path)

    def getNavigationInfo(self, ctx):
        return None

