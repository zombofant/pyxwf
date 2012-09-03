from __future__ import unicode_literals, print_function, absolute_import

import abc, operator, copy, os, logging

from PyXWF.utils import ET, _F
import PyXWF.Nodes as Nodes
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.Navigation as Navigation

import PyWeblog.Node as BlogNode
import PyWeblog.Protocols as Protocols

class TagDir(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info,
        Protocols.TagDir):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["tag-dir"]

    def __init__(self, site, parent, node):
        if not isinstance(parent, BlogNode.Blog):
            raise Errors.BadParent(self, parent)
        super(TagDir, self).__init__(site, parent, node)
        self.Blog = parent
        self.index = self.Blog.index

        self._children = {}
        self._childList = []

        self._navTitle = Types.NotNone(node.get("nav-title"))
        self._navDisplay = Navigation.DisplayMode(node.get("nav-display", "show"))
        self._showPagesInNav = Types.Typecasts.bool(node.get("show-pages-in-nav", False))
        self._pageTitleFmt = node.get("page-nav-title-format", "{tag} tag")
        self._listTemplate = Types.NotNone(node.get("list-template"))

        self._fixedChildren = {}
        for child in node:
            if child.tag == ET.Comment:
                continue
            if not child.get("name"):
                self._templateNode = child
                continue
            node = Registry.NodePlugins.getPluginInstance(child, site, self)
            if not isinstance(node, TagPage):
                raise Errors.BadChild(node, self)
            self._fixedChildren[node.Name] = node
        try:
            self._templateNode
        except AttributeError:
            raise Errors.NodeConfigurationError("Tag dir requires template node (<blog:tag-page /> without name)", self)

        self.Blog.TagDirectory = self

    def _getChildNode(self, key):
        if key == "":
            return self
        else:
            return self._children.get(key, None)

    def doGet(self, ctx):
        tagList = NS.PyBlog("tag-list")
        for posts, page in reversed(self._childList):
            tag = page.Name
            tagEl = ET.SubElement(tagList, NS.PyBlog.tag, attrib={
                "href": self.getTagPagePath(tag),
                "post-count": unicode(posts)
            })
            tagEl.text = tag
        return self.Site.templateCache[self._listTemplate].transform(tagList)

    def getTagPagePath(self, tag):
        return self.Path + tag

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self._navTitle

    def getDisplay(self):
        return self._navDisplay

    def getRepresentative(self):
        return self

    def resolvePath(self, ctx, relPath):
        node = super(TagDir, self).resolvePath(ctx, relPath)
        if node is self:
            ctx.useResource(self.Site.templateCache[self._listTemplate])
        return node

    def updateChildren(self):
        self._children = {}
        self._childList = [];
        for keyword, posts in self.index.getKeywordPosts():
            try:
                page = self._fixedChildren[keyword]
            except KeyError:
                self._templateNode.set("name", keyword)
                page = TagPage(self.Site, self, self._templateNode)
            self._children[keyword] = page
            self._childList.append((len(posts), page))
            page.updateChildren(posts)
        self._childList.sort(key=lambda x: (x[0], x[1].Name))
        logging.debug(_F("Tag dir updated: {0} children", len(self._childList)))
        logging.debug(_F("Tags: {0}", ", ".join(self._children.keys())))

    def __iter__(self):
        if self._showPagesInNav:
            return iter(page for count, page in self._childList)
        else:
            return iter([])

    def __len__(self):
        return len(self._childList)

    requestHandlers = {
        "GET": doGet
    }

class TagPage(Protocols.FeedableDirectoryMixin, Nodes.Node, Navigation.Info, Protocols.PostDirectory):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["tag-page"]

    SelectionCriterion = "tag"

    def __init__(self, site, parent, node):
        if not isinstance(parent, TagDir):
            raise Errors.BadParent(self, parent)
        super(TagPage, self).__init__(site, parent, node)
        self.Blog = parent.Blog
        self._posts = []
        self._title = (node.get("nav-title-fmt") or parent._pageTitleFmt).format(tag=self.Name)
        self._listTemplate = Types.NotNone(node.get("list-template"))
        self._feedsNode = None

    @property
    def SelectionValue(self):
        return self.Name

    def doGet(self, ctx):
        if not self._feedsNode and self.Blog.Feeds:
            feeds = self.Blog.Feeds.getFeedsNode(self)
            feeds.set("base", self.Path)
            self.abstracts.append(feeds)
            self._feedsNode = feeds
        return self.Site.templateCache[self._listTemplate].transform(
            self.abstracts,
            self.Blog.getTransformArgs()
        )

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self._title

    def getDisplay(self):
        return Navigation.Show

    def getRepresentative(self):
        return self

    def getPosts(self):
        return self._posts

    def updateChildren(self, posts):
        self._posts = list(reversed(posts))
        self.abstracts = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "tag": self.Name
        })
        for post in self._posts:
            self.abstracts.append(copy.deepcopy(post.abstract))

    requestHandlers = {
        "GET": doGet
    }

