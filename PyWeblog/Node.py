from __future__ import unicode_literals

import os, mimetypes, abc, itertools, copy, operator
from datetime import datetime
import time

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation
import PyWeb.Types as Types
import PyWeb.Errors as Errors
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS

import PyWeblog.Post as Post
import PyWeblog.Directories as Directories
import PyWeblog.LandingPage as LandingPage
import PyWeblog.TagPages as TagPages

class Blog(Nodes.DirectoryResolutionBehaviour, Nodes.Node):
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

        templates = node.find(NS.PyBlog.templates)
        if templates is None:
            templates = ET.Element(NS.PyBlog.templates)
        self.abstractListTemplate = self._loadTemplate(templates, "abstract-list")
        self.abstractTemplate = self._loadTemplate(templates, "abstract")
        self.postTemplate = self._loadTemplate(templates, "post")
        self.landingPageTemplate = self._loadTemplate(templates, "landing-page")
        self.tagDirTemplate = self._loadTemplate(templates, "tag-dir")

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

        self._pathDict = {
            "": self.landingPage,
            self.tagDir.Name: self.tagDir,
        }
        self._navChildren = [self.tagDir]

    def _loadTemplate(self, node, attr):
        templateFmt = "templates/blog/{0}.xsl"
        templateName = Types.DefaultForNone(templateFmt.format(attr))\
                                        (node.get(attr))
        return self.site.getTemplate(templateName)

    def _indexUpToDate(self):
        if not hasattr(self, "_allPosts"):
            return False
        return True

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
        self._allPosts.append(post)
        for tag in post.tags:
            self._tagCloud.setdefault(tag, []).append(post)
        return monthDir

    def removeFromIndex(self, post):
        self._allPosts.remove(post)
        year = post.creationDate.year
        yearDir = self._calendary[year]
        yearDir.remove(post)
        for tag in post.tags:
            self._tagCloud[tag].remove(post)

    def _clearIndex(self):
        self._allPosts = []
        self._tagCloud = {}
        self._categories = {}
        self._calendary = {}
        self._years = []

    def _createIndex(self):
        self._clearIndex()
        for dirpath, dirnames, filenames in os.walk(self.entriesDir):
            for filename in filenames:
                fullFile = os.path.join(dirpath, filename)
                post = Post.BlogPost(self, fullFile)
        self._allPosts.sort(key=lambda x: x.creationDate, reverse=True)

    def _getChildNode(self, key):
        try:
            return self._pathDict[key]
        except KeyError:
            pass
        if not self._indexUpToDate():
            self._createIndex()
        try:
            year = int(key)
            if str(year) != key:
                exc = Errors.MovedPermanently(newLocation=str(k))
                exc.local = True
                raise exc
            return self._calendary[year]
        except (ValueError, TypeError, KeyError):
            return None

    def iterRecent(self, count):
        if not self._indexUpToDate():
            self._createIndex()
        return itertools.islice(self._allPosts, 0, count)

    def getTagPath(self, tag):
        return self.tagDir.Path + "/" + tag

    def getTagsByPostCount(self):
        if not self._indexUpToDate():
            self._createIndex()
        return sorted(self._tagCloud.viewitems(),
            key=lambda x: len(x[1]), reverse=True)

    def getPostsByTag(self, tag):
        if not self._indexUpToDate():
            self._createIndex()
        try:
            return self._tagCloud[tag]
        except KeyError:
            return []

    def viewTagPosts(self):
        if not self._indexUpToDate():
            self._createIndex()
        return self._tagCloud.viewitems()

    def doGet(self, ctx):
        if not self._indexUpToDate():
            self._createIndex()
        raise Errors.Found(newLocation=self._years[0].Path)

    def getNavigationInfo(self, ctx):
        return self.landingPage.getNavigationInfo(ctx)

    def getTitle(self):
        return self.navTitle

    def getDisplay(self):
        return self.navDisplay

    def __iter__(self):
        if not self._indexUpToDate():
            self._createIndex()
        return itertools.chain(
            self._years,
            self._navChildren
        )

    requestHandlers = {
        "GET": doGet
    }
