from PyWeb.utils import ET
import PyWeb.Namespaces as NS
import PyWeb.Nodes as Nodes
import PyWeb.Types as Types
import PyWeb.Navigation as Navigation
import PyWeb.Errors as Errors

import PyWeblog.Atom as Atom
import PyWeblog.Directories as Directories

class TagPage(Nodes.Node, Navigation.Info):
    __metaclass__ = Nodes.NodeMeta

    def __init__(self, tagDir, tag):
        super(TagPage, self).__init__(tagDir.site, tagDir, None)
        self.blog = tagDir.blog
        self.tag = tag
        self._path = self.parent.Path + "/" + tag
        self.feedNode = Atom.AtomFeedNode(self, self.tag, "tag")
        self._feedTitle = tagDir._pageFeedTitle.format(tag=self.tag)

    @property
    def Name(self):
        return self.tag

    def getPosts(self):
        return self.blog.getPostsByTag(self.tag)

    def resolvePath(self, ctx, relPath):
        self.posts = self.getPosts()
        ctx.useResources(self.posts)
        if len(self.posts) == 0:
            self.posts = self.getPosts()
            ctx.useResources(self.posts)
        if len(self.posts) == 0:
            raise Errors.NotFound()
        if relPath == "":
            queryInfo = ctx.QueryData
            if "feed" in queryInfo:
                feed = queryInfo["feed"]
                if len(feed) > 1:
                    raise Errors.BadRequest()
                feed = feed[0]
                if feed == "atom":
                    return self.feedNode.resolvePath(ctx, "")
                else:
                    raise Errors.NotFound()
            elif not queryInfo:
                return super(TagPage, self).resolvePath(ctx, relPath)
            else:
                raise Errors.BadRequest()

    def doGet(self, ctx):
        posts = self.posts
        abstractList = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "kind": "tag",
            "title": self.tag,
            "feed-path": self.Path + "?feed=atom"
        })
        for post in sorted(posts, key=lambda x: x.creationDate, reverse=True):
            abstractList.append(post.getAbstract(ctx))
        doc = self.blog.AbstractListTemplate.transform(abstractList, {})
        if self.blog.atomFeed:
            doc.links.append(self.blog.atomFeed.Link(
                self.Path + "?feed=atom",
                self._feedTitle
            ))
        return doc

    def __len__(self):
        return len(self.getPosts())

    def getTitle(self):
        return self.tag

    def getDisplay(self):
        return Navigation.Show

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        return self

    requestHandlers = {
        "GET": doGet
    }

class TagDir(Directories.BlogFakeDir):
    __metaclass__ = Nodes.NodeMeta

    def __init__(self, blog, node):
        super(TagDir, self).__init__(blog, blog, node=node)
        self._tagPages = {}
        self._navTitle = Types.DefaultForNone(self._name,
            Types.Typecasts.unicode)(node.get("nav-title"))
        self._navDisplay = Types.DefaultForNone(Navigation.Hidden,
            Navigation.DisplayMode)(node.get("nav-display"))
        self._pageFeedTitle = Types.DefaultForNone("Posts with tag \"{tag}\"",
            Types.Typecasts.unicode)(node.get("page-feed-title"))

    def _getChildNode(self, key):
        if key == "":
            return self
        try:
            return self.getTagPage(key)
        except KeyError:
            return None

    def getTagPage(self, tag):
        try:
            return self._tagPages[tag]
        except KeyError:
            posts = self.blog.getPostsByTag(tag)
        if len(posts) == 0:
            return TagPage(self, tag)  # not store it anywhere
        else:
            tagPage = TagPage(self, tag)
            self._tagPages[tag] = tagPage
            return tagPage

    def doGet(self, ctx):
        tagList = ET.Element(getattr(NS.PyBlog, "tag-list"))
        for tag, posts in self.blog.getTagsByPostCount():
            count = len(posts)
            if count == 0:
                continue
            tagEl = ET.SubElement(tagList, NS.PyBlog.tag, attrib={
                "href": self.getTagPage(tag).Path,
                "post-count": unicode(len(posts))
            })
            tagEl.text = tag
        return self.blog.TagDirTemplate.transform(tagList, {})

    def __len__(self):
        return len(self.blog._tagCloud)

    def getTitle(self):
        return self._navTitle

    def getDisplay(self):
        return self._navDisplay

    requestHandlers = {
        "GET": doGet
    }
