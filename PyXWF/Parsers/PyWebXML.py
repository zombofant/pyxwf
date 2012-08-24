# encoding=utf-8
from __future__ import unicode_literals

import itertools
from datetime import datetime

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Registry as Registry
import PyXWF.Parsers as Parsers
import PyXWF.Document as Document
import PyXWF.Namespaces as NS


map = itertools.imap


class PyWebXML(Parsers.ParserBase):
    __metaclass__ = Registry.SitletonMeta

    mimeTypes = ["application/x-pywebxml"]

    def __init__(self, site):
        super(PyWebXML, self).__init__(site,
            parserMimeTypes=self.mimeTypes
        )

    @staticmethod
    def _linkFromNode(node):
        return Link.create(
            node.get("rel"), node.get("type"), node.get("href"), node.get("media")
        )

    @classmethod
    def getLinks(cls, meta):
        return list(meta.findall(NS.PyWebXML.link))

    @classmethod
    def getKeywords(cls, meta):
        return list(map(
            lambda node: unicode(node.text), meta.findall(NS.PyWebXML.kw)))

    @classmethod
    def getKeywordsAndLinks(cls, meta):
        """
        Deprecated – do not use.
        """
        return cls.getKeywords(meta), cls.getLinks(meta)

    @classmethod
    def getAuthors(cls, meta):
        return list(map(Document.Author.fromNode, meta.findall(NS.PyWebXML.author)))

    @classmethod
    def getDate(cls, meta):
        datetext = meta.findtext(NS.PyWebXML.date)
        return utils.parseISODate(datetext)

    @classmethod
    def getMeta(cls, meta):
        return meta.findall(NS.XHTML.meta)

    def parseTree(self, root, headerOffset=1):
        if root.tag != NS.PyWebXML.page:
            raise ValueError("This is not a pyxwf-xml document.")

        meta = root.find(NS.PyWebXML.meta)
        if meta is None:
            raise ValueError("Metadata is missing.")

        title = unicode(meta.findtext(NS.PyWebXML.title))
        if title is None:
            raise ValueError("Title is missing.")

        keywords, links = self.getKeywordsAndLinks(meta)

        body = root.find(NS.XHTML.body)
        if body is None:
            raise ValueError("No body tag found")
        self.transformHeaders(body, headerOffset)

        date = self.getDate(meta)
        authors = self.getAuthors(meta)
        hmeta = self.getMeta(meta)

        ext = meta

        return Document.Document(title, keywords, links, body,
            ext=ext, date=date, authors=authors, hmeta=hmeta)

    def parse(self, fileref, **kwargs):
        tree = ET.parse(fileref)
        root = tree.getroot()
        return self.parseTree(root, **kwargs)
