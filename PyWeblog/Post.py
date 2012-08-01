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
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS

class BlogPost(Nodes.Node, Navigation.Info):
    __metaclass__ = Nodes.NodeMeta

    def _processFile(self, fileName):
        mimeType, encoding = mimetypes.guess_type(fileName, strict=False)
        documentHandler = Registry.DocumentPlugins(mimeType)
        return documentHandler.parse(fileName)

    def _processDocument(self, doc):
        ext = doc.ext
        date = doc.date
        if date is None:
            # fall back to last modified
            date = doc.lastModified
        self.creationDate = date
        self.authors = doc.authors

    def _reload(self, initial=False):
        if not initial:
            self.blog.removeFromIndex(self)
        doc = self._processFile(self.fileName)
        self._processDocument(doc)
        urlName = os.path.basename(self.fileName)
        self._name = os.path.splitext(urlName)[0]
        self.tags = list(doc.keywords)
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
        article = document.toPyWebXMLPage()
        meta = article.find(NS.PyWebXML.meta)
        nodePath = ET.SubElement(meta, getattr(NS.PyBlog, "node-path"))
        nodePath.text = self.Path
        abstractText = ET.SubElement(meta, getattr(NS.PyBlog, "abstract-text"))
        abstractText.text = unicode(document.ext.findtext(NS.PyBlog.abstract))
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
        result = self.abstract
        if result is None:
            result = self._createAbstract()
        return result

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
