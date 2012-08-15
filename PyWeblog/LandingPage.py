from __future__ import unicode_literals

from PyWeb.utils import ET
import PyWeb.Types as Types
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS

import PyWeblog.Atom as Atom
import PyWeblog.Directories as Directories


class LandingPage(Directories.WithFeedMixin, Nodes.Node, Navigation.Info):
    __metaclass__ = Nodes.NodeMeta

    def __init__(self, blog, node):
        super(LandingPage, self).__init__(blog.site, blog, node)
        if self._name != "":
            raise ValueError("Invalid landing page name.")
        self.blog = blog
        self.recentCount = Types.DefaultForNone(3,
            Types.NumericRange(Types.Typecasts.int, 1, None)
        )(node.get("post-count"))
        self.templateName = Types.NotNone(node.get("list-template"))
        self.feedNode = Atom.AtomFeedNode(self, "", "")

    def getPosts(self):
        return list(self.blog.iterRecent(self.recentCount))

    def resolvePath(self, ctx, relPath):
        self.posts = self.getPosts()
        ctx.useResources(self.posts)
        self.template = self.blog.site.templateCache[self.templateName]
        ctx.useResource(self.template)
        return super(LandingPage, self).resolvePath(ctx, relPath)

    def doGet(self, ctx):
        articles = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "feed-path": self.Path + "?feed=atom"
        })
        for recentPost in self.posts:
            articles.append(recentPost.getAbstract(ctx))
        return self.template.transform(articles, {})

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self.blog.getTitle()

    def getDisplay(self):
        return self.blog.getDisplay()

    def getRepresentative(self):
        return self

    def __iter__(self):
        return iter(self.blog)

    requestHandlers = {
        "GET": doGet
    }
