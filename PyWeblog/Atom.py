from __future__ import unicode_literals

from PyWeb.utils import ET
import PyWeb.ContentTypes as ContentTypes
import PyWeb.Types as Types
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS

class AtomFeedRoot(object):
    def __init__(self, cfgNode, blog):
        super(AtomFeedRoot, self).__init__()
        self.blog = blog
        self.site = blog.site

        self.templateName = Types.NotNone(cfgNode.get("template"))
        self.rootId = cfgNode.get("root-id")
        self.linkPrefix = Types.NotNone(cfgNode.get("link-prefix"))
        self.idPrefix = cfgNode.get("id-prefix", self.linkPrefix)
        self.limit = Types.NumericRange(Types.Typecasts.int, 1, None)(cfgNode.get("limit"))

    def prepare(self, ctx, posts):
        ctx.useResources(posts)
        self.template = self.blog.site.templateCache[self.templateName]
        ctx.useResource(self.template)

    def render(self, ctx, posts, title, kind):
        root = ET.Element(NS.PyBlog.syndication)
        root.set("title", title)
        root.set("kind", kind)
        rootID = ET.SubElement(root, NS.PyBlog.id)
        rootID.text = self.rootId or (self.idPrefix + self.blog.Path)
        for post in posts:
            postNode = ET.SubElement(root, NS.PyBlog.post)
            postID = ET.SubElement(postNode, NS.PyBlog.id)
            postID.text = self.idPrefix + post.Path
            postNode.append(post.getArticle())

        self.site.transformReferences(ctx, root)
        feed = self.template.rawTransform(root, {})
        self.site.transformPyNamespace(ctx, feed, crumbs=False, link=False)
        for localLink in feed.iter(NS.PyWebXML.link):
            localLink.tag = NS.Atom.link
            self.site.transformHref(localLink)
            localLink.set("href", self.linkPrefix[:-1]+localLink.get("href"))
        return feed

class AtomFeedNode(Nodes.Node):
    def __init__(self, blogDir, title, kind):
        super(AtomFeedNode, self).__init__(blogDir.site, blogDir, None)
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
        return self.feedRoot.render(ctx, self.posts, self.title, self.kind)

    def getNavigationInfo(self, ctx):
        return None

