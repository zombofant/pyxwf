from __future__ import unicode_literals

import os, mimetypes, abc, itertools, copy
from datetime import datetime
import time

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Types as Types
import PyWeb.Errors as Errors
import PyWeb.Document as Document
import PyWeb.Cache as Cache
import PyWeb.Namespaces as NS

class BlogFakeDir(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info):
    def __init__(self, blog, parent, name):
        super(BlogFakeDir, self).__init__(blog.site, parent, None)
        self.blog = blog
        self._name = unicode(name)
        self._path = parent.Path + "/" + name

    def getTitle(self):
        return self._name

    def getDisplay(self):
        return Navigation.Show if len(self) > 0 else Navigation.Hidden

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        return self

class BlogYearDir(BlogFakeDir):
    def __init__(self, blog, year):
        super(BlogYearDir, self).__init__(blog, blog, str(year))
        self._year = year
        self.months = [None] * 12
        self.monthType = Types.NumericRange(int, 1, 12)

    def _validMonthIter(self, reverse=False):
        if reverse:
            return itertools.ifilter(lambda x: x is not None, reversed(self.months))
        else:
            return itertools.ifilter(lambda x: x is not None, self.months)

    def remove(self, post):
        month = post.creationDate.month
        monthDir = self.months[month]
        monthDir.remove(post)

    def doGet(self, ctx):
        try:
            highestMonth = next(iter(self._validMonthIter(reverse=True)))
        except StopIteration:
            raise Errors.NotFound()
        raise Errors.Found(newLocation=highestMonth.Path)

    def _getChildNode(self, key):
        if key == "":
            return self
        else:
            try:
                return self.months[int(key)]
            except (ValueError, TypeError) as err:
                return None

    def __getitem__(self, month):
        month = self.monthType(month) - 1
        monthObj = self.months[month]
        if monthObj is None:
            monthObj = BlogMonthDir(self, month)
            self.months[month] = monthObj
        return monthObj

    def __iter__(self):
        return iter(self._validMonthIter())

    def __len__(self):
        return sum(1 for _ in self._validMonthIter())

    requestHandlers = {
        "GET": doGet
    }

class BlogMonthDir(BlogFakeDir):
    __metaclass__ = Nodes.NodeMeta

    def __init__(self, yearDir, month):
        super(BlogMonthDir, self).__init__(yearDir.blog, yearDir, str(month))
        self._month = month
        self.pathDict = {}
        self.children = []

    def add(self, post):
        if post.Name in self.pathDict:
            raise ValueError("Duplicate name: {0}".format(post.Name))
        self.children.append(post)
        self.children.sort(key=lambda x: x.creationDate)
        self.pathDict[post.Name] = post

    def remove(self, post):
        del self.pathDict[post.Name]
        self.children.remove(post)

    def checkNotModified(self, ctx):
        highestTimestamp = None
        # some items might get deleted during this
        for post in list(self.children):  
            post.update()
            if highestTimestamp:
                highestTimestamp = max(post.lastModified, highestTimestamp)
            else:
                highestTimestamp = post.lastModified
        ctx.checkNotModified(highestTimestamp)

    def doGet(self, ctx):
        self.checkNotModified(ctx)
        abstractList = ET.Element(getattr(NS.PyBlog, "abstract-list"))
        for post in self.children:
            abstractList.append(post.getAbstract(ctx))
        return self.blog.abstractListTemplate.transform(abstractList, {
            b"year": str(self.parent._year),
            b"month": str(self._month),
            b"month_name": utils.unicodeToXPathStr(self.getTitle())
        })

    def getTitle(self):
        return time.strftime("%B", (2000, self._month, 1, 0, 0, 0, 0, 0, -1))

    def _getChildNode(self, key):
        if key == "":
            return self
        return self.pathDict.get(key, None)

    def __len__(self):
        return len(self.children)

    requestHandlers = {
        "GET": doGet
    }
    

class BlogPost(Nodes.Node, Navigation.Info):
    __metaclass__ = Nodes.NodeMeta

    def _processFile(self, fileName):
        mimeType, encoding = mimetypes.guess_type(fileName, strict=False)
        try:
            documentHandler = Registry.DocumentPlugins(mimeType)
        except KeyError:
            print("invalid post (no doc handler for {0})".format(mimeType))
            return
        return documentHandler.parse(fileName)

    def _processDocument(self, doc):
        ext = doc.ext
        date = ext.find(NS.PyBlog.date)
        if date is None:
            # fall back to last modified
            self.creationDate = doc.lastModified
        else:
            self.creationDate = datetime(
                Types.Typecasts.int(date.get("y")),
                Types.Typecasts.int(date.get("m")),
                Types.Typecasts.int(date.get("d")),
                Types.Typecasts.int(date.get("hr")),
                Types.Typecasts.int(date.get("min"))
            )
        self.author = ext.findtext(NS.PyBlog.author)

    def _reload(self, initial=False):
        if not initial:
            self.blog.removeFromIndex(self)
        doc = self._processFile(self.fileName)
        self._processDocument(doc)
        urlName = os.path.basename(self.fileName)
        self._name = os.path.splitext(urlName)[0]
        parent = self.blog.addToIndex(self)
        self._path = parent.Path + "/" + self._name
        self.post = None
        self.abstract = None
        self._createBlogTree(doc)
        self.lastModified = doc.lastModified
        return doc, parent, self._name, self._path

    def __init__(self, blog, fileName):
        self.fileName = fileName
        self.blog = blog
        document, parent, name, path = self._reload(initial=True)
        super(BlogPost, self).__init__(blog.site, parent, None)
        self._path = path
        self._name = name

    def _createBlogTree(self, document):
        article = ET.Element(NS.PyBlog.article)
        datetime = ET.SubElement(article, NS.PyBlog.datetime)
        datetime.text = self.creationDate.isoformat()
        article.append(document.body)
        nodePath = ET.SubElement(article, getattr(NS.PyBlog, "node-path"))
        nodePath.text = self.Path
        title = ET.SubElement(article, NS.PyBlog.title)
        title.text = document.title
        abstractText = ET.SubElement(article, getattr(NS.PyBlog, "abstract-text"))
        abstractText.text = unicode(document.ext.findtext(NS.PyBlog.abstract))
        if self.author is not None:
            author = ET.SubElement(article, NS.PyBlog.author)
            author.text = self.author
        self.article = article

    def _createPost(self):
        date_long = self.creationDate.strftime(self.site.longDateFormat)
        self.post = self.blog.postTemplate.transform(self.article, {
            b"date_long": utils.unicodeToXPathStr(date_long)
        })
        self.post.lastModified = self.lastModified
        return self.post

    def _createAbstract(self):
        date_long = self.creationDate.strftime(self.site.longDateFormat)
        self.abstract = self.blog.abstractTemplate.xsltTransform(self.article,
            date_long=utils.unicodeToXPathStr(date_long)
        ).getroot()
        return self.abstract

    def update(self):
        fileModified = utils.fileLastModified(self.fileName)
        if fileModified is None:  # deleted
            self.blog.delete(self)
            return False
        if fileModified > self.lastModified:
            _, parent, _, _ = self._reload()
            self._parent = parent

    def doGet(self, ctx):
        self.update()
        ctx.checkNotModified(self.lastModified)
        return self.post or self._createPost()

    def getAbstract(self, ctx):
        return self.abstract or self._createAbstract()

    def getTitle(self):
        return (self.post or self._createPost()).title

    def getDisplay(self):
        return Navigation.Show

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        return self

    requestHandlers = {
        "GET": doGet
    }

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
            yearDir = BlogYearDir(self, year)
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
                post = BlogPost(self, fullFile)
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
