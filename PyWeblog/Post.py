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
import PyWeb.Resource as Resource

class BlogPost(Nodes.Node, Navigation.Info, Resource.Resource):
    __metaclass__ = Nodes.NodeMeta

    def _processDocument(self, docRef):
        doc = docRef.doc
        ext = doc.ext
        date = doc.date
        if date is None:
            # fall back to last modified
            date = doc.LastModified
        self.creationDate = date
        self.authors = doc.authors
        self.tags = list(doc.keywords)

    def _reload(self, initial=False):
        if not initial:
            self.blog.removeFromIndex(self)
        docRef = self.site.fileDocumentCache.get(self.fileName, headerOffset=2)
        self._processDocument(docRef)

        urlName = os.path.basename(self.fileName)
        self._name = os.path.splitext(urlName)[0]

        parent = self.blog.addToIndex(self)

        self._path = parent.Path + "/" + self._name
        self.post = None
        self.abstract = None
        self._createBlogTree(docRef.doc)
        self._lastModified = docRef.LastModified

        docRef.proposeUncache()
        return parent, self._name, self._path

    def __init__(self, blog, fileName):
        self.fileName = fileName
        self.blog = blog
        self.site = blog.site
        parent, name, path = self._reload(initial=True)
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

        for kw in meta.findall(NS.PyWebXML.kw):
            kw.set("href", self.blog.getTagPath(kw.text))

        self.article = article

    def _createPost(self):
        date_long = self.creationDate.strftime(self.site.longDateFormat)
        self.post = self.blog.PostTemplate.transform(self.article, {
            b"date_long": utils.unicodeToXPathStr(date_long)
        })
        return self.post

    def _createAbstract(self):
        date_long = self.creationDate.strftime(self.site.longDateFormat)
        self.abstract = self.blog.AbstractTemplate.xsltTransform(self.article,
            date_long=utils.unicodeToXPathStr(date_long)
        ).getroot()
        return self.abstract

    @property
    def LastModified(self):
        return self._lastModified

    def update(self):
        fileModified = utils.fileLastModified(self.fileName)
        if fileModified is None:  # deleted
            self.blog.delete(self)
            return
        if fileModified > self._lastModified:
            parent, _, _ = self._reload()
            self._parent = parent

    def resolvePath(self, ctx, relPath):
        ctx.useResource(self)
        return super(BlogPost, self).resolvePath(ctx, relPath)

    def doGet(self, ctx):
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
