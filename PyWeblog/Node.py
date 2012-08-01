from __future__ import unicode_literals

import os, mimetypes, abc, itertools, copy
from datetime import datetime
import time

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation
import PyWeb.Types as Types
import PyWeb.Errors as Errors
import PyWeb.Document as Document
import PyWeb.Cache as Cache
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS
import PyWeblog.Post as Post
import PyWeblog.Directories as Directories

class Blog(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info):
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

        templateFmt = "templates/blog/{0}.xsl"
        templates = node.find(NS.PyBlog.templates)
        if templates is None:
            templates = ET.Element(NS.PyBlog.templates)
        self.abstractListTemplate = \
            self._loadTemplate(templates, "abstract-list", templateFmt)
        self.abstractTemplate = \
            self._loadTemplate(templates, "abstract", templateFmt)
        self.postTemplate = \
            self._loadTemplate(templates, "post", templateFmt)

        structure = node.find(NS.PyBlog.structure)
        self.combinedStyle = Types.DefaultForNone(False, Types.EnumMap({
            "year+month": True,
            "separate": False
        }))(structure.get("nav"))
        self.showPostsInNav = Types.DefaultForNone(False,
            Types.Typecasts.bool
        )(structure.get("show-posts-in-nav"))

    def _loadTemplate(self, node, attr, defaultFmt):
        templateName = Types.DefaultForNone(defaultFmt.format(attr))\
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
        return monthDir

    def removeFromIndex(self, post):
        self._allPosts.remove(post)
        year = post.creationDate.year
        yearDir = self._calendary[year]
        yearDir.remove(post)

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
        self._allPosts.sort(key=lambda x: x.creationDate)

    def _getChildNode(self, key):
        if key == "":
            return self
        else:
            if not self._indexUpToDate():
                self._createIndex()
            try:
                k = int(key)
                if str(k) != key:
                    exc = Errors.MovedPermanently(newLocation=str(k))
                    exc.local = True
                    raise exc
                return self._calendary[k]
            except (ValueError, TypeError, KeyError):
                return None

    def doGet(self, ctx):
        if not self._indexUpToDate():
            self._createIndex()
        raise Errors.Found(newLocation=self._years[0].Path)

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self.navTitle

    def getDisplay(self):
        return self.navDisplay

    def getRepresentative(self):
        return self

    def __iter__(self):
        if not self._indexUpToDate():
            self._createIndex()
        return iter(self._years)

    requestHandlers = {
        "GET": doGet
    }
