from __future__ import unicode_literals

import os, mimetypes, abc, itertools, copy, operator
from datetime import datetime
import time

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Registry as Registry
import PyXWF.Navigation as Navigation
import PyXWF.Types as Types
import PyXWF.Errors as Errors
import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation
import PyXWF.Namespaces as NS
import PyXWF.Resource as Resource
import PyXWF.TimeUtils as TimeUtils

import PyWeblog.Post as Post
import PyWeblog.Atom as Atom
import PyWeblog.Directories as Directories
import PyWeblog.LandingPage as LandingPage
import PyWeblog.TagPages as TagPages

try:
    from blist import sortedlist

    class SortedPostList(sortedlist):
        def __init__(self, iterable=[]):
            super(SortedPostList, self).__init__(iterable)
except ImportError:
    class SortedPostList(list):
        def add(self, post):
            self.append(post)
            self.sort()

class Blog(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Resource.Resource):
    __metaclass__ = Registry.NodeMeta

    namespace = unicode(NS.PyBlog)
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Blog, self).__init__(site, parent, node)
        self.entriesDir = os.path.join(site.root,
            Types.Typecasts.unicode(node.get("entries-dir")))
        self.indexFile = node.get("index-file")
        self.navTitle = Types.Typecasts.unicode(node.get("nav-title"))
        self.navDisplay = Types.DefaultForNone(Navigation.Show,
            Navigation.DisplayMode)(node.get("nav-display"))
        self._reloadTrigger = Types.DefaultForNone("blog.reload")\
            (node.get("index-trigger"))
        self._reloadTrigger = os.path.join(self.entriesDir, self._reloadTrigger)

        templates = node.find(NS.PyBlog.templates)
        if templates is None:
            templates = ET.Element(NS.PyBlog.templates)
        self.abstractListTemplate = self._cfgTemplate(templates, "abstract-list")
        self.abstractTemplate = self._cfgTemplate(templates, "abstract")
        self.postTemplate = self._cfgTemplate(templates, "post")
        self.tagDirTemplate = self._cfgTemplate(templates, "tag-dir")

        structure = node.find(NS.PyBlog.structure)
        self.combinedStyle = Types.DefaultForNone(False, Types.EnumMap({
            "year+month": True,
            "separate": False
        }))(structure.get("nav"))
        self.showPostsInNav = Types.DefaultForNone(False,
            Types.Typecasts.bool
        )(structure.get("show-posts-in-nav"))

        landingPage = node.find(getattr(NS.PyBlog, "landing-page"))
        if landingPage is None:
            landingPage = ET.Element(getattr(NS.PyBlog, "landing-page"))
        landingPage.set("name", "")
        self.landingPage = LandingPage.LandingPage(self, landingPage)

        tagDir = node.find(getattr(NS.PyBlog, "tag-dir"))
        if tagDir is None:
            tagDir = ET.Element(getattr(NS.PyBlog, "tag-dir"))
        self.tagDir = TagPages.TagDir(self, tagDir)

        atomFeed = node.find(getattr(NS.PyBlog, "atom"))
        if atomFeed is None:
            self.atomFeed = None
        else:
            self.atomFeed = Atom.AtomFeedRoot(atomFeed, self)

        self._pathDict = {
            "": self.landingPage,
            self.tagDir.Name: self.tagDir,
        }
        self._navChildren = [self.tagDir]

        if not os.path.isfile(self._reloadTrigger):
            open(self._reloadTrigger, "w").close()

        self._lastIndexUpdate = None
        self._lastTrigger = None

    def _cfgTemplate(self, node, attr):
        templateFmt = "templates/{0}/{1}.xsl"
        return Types.DefaultForNone(templateFmt.format(self.Name, attr))\
                (node.get(attr))

    @property
    def AbstractListTemplate(self):
        return self.site.templateCache[self.abstractListTemplate]

    @property
    def AbstractTemplate(self):
        return self.site.templateCache[self.abstractTemplate]

    @property
    def PostTemplate(self):
        return self.site.templateCache[self.postTemplate]

    @property
    def LandingPageTemplate(self):
        return self.site.templateCache[self.landingPageTemplate]

    @property
    def TagDirTemplate(self):
        return self.site.templateCache[self.tagDirTemplate]

    @property
    def LastModified(self):
        return self._lastIndexUpdate

    def update(self):
        indexTriggerDate = utils.fileLastModified(self._reloadTrigger)
        if self._lastTrigger is None or \
                indexTriggerDate > self._lastTrigger:
            self._lastTrigger = indexTriggerDate
            self._createIndex()

    def addToIndex(self, post):
        year = post.creationDate.year
        month = post.creationDate.month
        yearDir = self._calendary.get(year, None)
        if yearDir is None:
            yearDir = Directories.BlogYearDir(self, year)
            self._calendary[year] = yearDir
            self._years.append(yearDir)
            self._years.sort(key=lambda x: x._year)
        monthDir = yearDir[month+1]
        monthDir.add(post)
        self._allPosts.add(post)
        for tag in post.tags:
            self._tagCloud.setdefault(tag, []).append(post)
        self._lastIndexUpdate = TimeUtils.stripMicroseconds(datetime.utcnow())
        return monthDir

    def removeFromIndex(self, post):
        self._allPosts.remove(post)
        year = post.creationDate.year
        yearDir = self._calendary[year]
        yearDir.remove(post)
        for tag in post.tags:
            self._tagCloud[tag].remove(post)
        self._lastIndexUpdate = TimeUtils.stripMicroseconds(datetime.utcnow())

    def _clearIndex(self):
        self._allPosts = SortedPostList()
        self._tagCloud = {}
        self._categories = {}
        self._calendary = {}
        self._years = []

    def _createIndex(self):
        self._clearIndex()
        for dirpath, dirnames, filenames in os.walk(self.entriesDir):
            for filename in filenames:
                fullFile = os.path.join(dirpath, filename)
                try:
                    post = Post.BlogPost(self, fullFile)
                except (Errors.MissingParserPlugin, Errors.UnknownMIMEType):
                    pass

    def _getChildNode(self, key):
        try:
            return self._pathDict[key]
        except KeyError:
            pass
        try:
            year = int(key)
            if str(year) != key:
                exc = Errors.MovedPermanently(newLocation=str(k))
                exc.local = True
                raise exc
            return self._calendary[year]
        except (ValueError, TypeError, KeyError):
            return None

    def resolvePath(self, ctx, relPath):
        ctx.useResource(self)  # as even 404 may be dependent on our index state
        return super(Blog, self).resolvePath(ctx, relPath)

    def iterRecent(self, count):
        return itertools.islice(self._allPosts, 0, count)

    def getTagPath(self, tag):
        return self.tagDir.Path + "/" + tag

    def getTagsByPostCount(self):
        return sorted(self._tagCloud.viewitems(),
            key=lambda x: len(x[1]), reverse=True)

    def getPostsByTag(self, tag):
        try:
            return self._tagCloud[tag]
        except KeyError:
            return []

    def getPreviousAndNext(self, post):
        posts = self._allPosts
        index = posts.index(post)
        # cannot do try-except here, otherwise we get the last element from the
        # list!
        if index > 0:
            next = posts[index-1]
        else:
            next = None
        try:
            prev = posts[index+1]
        except IndexError:
            prev = None
        return (prev, next)

    def viewTagPosts(self):
        return self._tagCloud.viewitems()

    def doGet(self, ctx):
        raise Errors.Found(newLocation=self._years[0].Path)

    def getNavigationInfo(self, ctx):
        return self.landingPage.getNavigationInfo(ctx)

    def getTitle(self):
        return self.navTitle

    def getDisplay(self):
        return self.navDisplay

    def __iter__(self):
        return itertools.chain(
            self._years,
            self._navChildren
        )

    requestHandlers = {
        "GET": doGet
    }
