# encoding=utf-8
from __future__ import unicode_literals

import itertools
from datetime import datetime

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Parsers as Parsers
import PyWeb.Document as Document
import PyWeb.Namespaces as NS


map = itertools.imap

class Link(object):
    _linkTag = "{{{0}}}link".format(NS.xhtml)
    _scriptTag = "{{{0}}}script".format(NS.xhtml)

    @classmethod
    def create(cls, rel, typeName, href, media=None):
        if rel == "stylesheet":
            link = ET.Element(cls._linkTag, attrib={
                "rel": "stylesheet",
                "type": typeName,
                "href": href
            })
            if media:
                link.set("media", media)
            return link
        elif rel == "script":
            return ET.Element(cls._scriptTag, attrib={
                "type": typeName,
                "src": href
            })
        else:
            raise KeyError("Unknown link relation: {0}".format(rel))


class PyWebXML(Parsers.ParserBase):
    __metaclass__ = Registry.ParserMeta

    mimeTypes = ["application/x-pyweb-xml"]

    def __init__(self, mime):
        super(PyWebXML, self).__init__()

    @staticmethod
    def _linkFromNode(node):
        return Link.create(
            node.get("rel"), node.get("type"), node.get("href"), node.get("media")
        )

    @classmethod
    def getLinks(cls, meta):
        return list(map(cls._linkFromNode, meta.findall(NS.PyWebXML.link)))

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

    def parse(self, fileref, headerOffset=1):
        tree = ET.parse(fileref)
        root = tree.getroot()
        if root.tag != NS.PyWebXML.page:
            raise ValueError("This is not a pyweb-xml document.")

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

        ext = meta

        return Document.Document(title, keywords, links, body,
            ext=ext, date=date, authors=authors)
