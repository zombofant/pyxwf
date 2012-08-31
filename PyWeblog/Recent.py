from __future__ import unicode_literals, print_function, absolute_import

import itertools, copy

from PyXWF.utils import ET
import PyXWF.Nodes as Nodes
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.Navigation as Navigation

import PyWeblog.Node as BlogNode
import PyWeblog.Protocols as Protocols

class RecentPosts(Protocols.FeedableDirectoryMixin, Nodes.Node, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["recent"]

    _postCountType = Types.NumericRange(int, 1, None)

    SelectionCriterion = ""
    SelectionValue = ""

    def __init__(self, site, parent, node):
        if not isinstance(parent, BlogNode.Blog):
            raise Errors.BadParent(self, parent)
        super(RecentPosts, self).__init__(site, parent, node)
        self.Blog = parent

        self._navTitle = Types.NotNone(node.get("nav-title"))
        self._navDisplay = Navigation.DisplayMode(node.get("nav-display", "show"))
        self._listTemplate = Types.NotNone(node.get("list-template"))
        self._postCount = self._postCountType(node.get("post-count"))

    def resolvePath(self, ctx, relPath):
        result = super(RecentPosts, self).resolvePath(ctx, relPath)
        if result is self:
            ctx.useResource(self.Blog.index)
            ctx.useResource(self.Site.templateCache[self._listTemplate])
        return result

    def doGet(self, ctx):
        abstracts = NS.PyBlog("abstract-list")
        if self.Blog.Feeds:
            feeds = self.Blog.Feeds.getFeedsNode(self)
            feeds.set("base", self.Path)
            abstracts.append(feeds)
        postIter = itertools.islice(
            reversed(self.Blog.index.getAllPosts()),
            0,
            self._postCount
        )
        for post in postIter:
            abstracts.append(copy.deepcopy(post.abstract))
        return self.Site.templateCache[self._listTemplate].transform(
            abstracts,
            self.Blog.getTransformArgs()
        )

    def getPosts(self):
        return reversed(self.Blog.index.getAllPosts())

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self._navTitle

    def getDisplay(self):
        return self._navDisplay

    def getRepresentative(self):
        return self

    requestHandlers = {
        "GET": doGet
    }

