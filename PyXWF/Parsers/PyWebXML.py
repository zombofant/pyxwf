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
    """
    This class parses PyWebXML documents. Usually, you don't create instances of
    this, you just access it using via the :attr:`~PyXWF.Site.parser_registry`
    attribute of your :class:`~PyXWF.Site` instance.
    """
    __metaclass__ = Registry.SitletonMeta

    mimetypes = ["application/x-pywebxml"]

    def __init__(self, site):
        super(PyWebXML, self).__init__(site,
            parser_mimetypes=self.mimetypes
        )

    def _link_from_node(self, node):
        if node.get("rel") == "script":
            href = self.site.transform_relative_uri(None, node.get("href") or "")
            return ET.Element(NS.XHTML.script, attrib={
                "type": node.get("type") or "",
                "src": href
            })
        else:
            return node

    def get_links(self, meta):
        return list(map(self._link_from_node, meta.findall(NS.PyWebXML.link)))

    @classmethod
    def get_keywords(cls, meta):
        return list(map(
            lambda node: unicode(node.text), meta.findall(NS.PyWebXML.kw)))

    @classmethod
    def get_authors(cls, meta):
        return list(map(Document.Author.from_node, meta.findall(NS.PyWebXML.author)))

    @classmethod
    def get_date(cls, meta):
        datetext = meta.findtext(NS.PyWebXML.date)
        return utils.parse_iso_date(datetext)

    @classmethod
    def get_meta(cls, meta):
        return meta.findall(NS.XHTML.meta)

    @classmethod
    def get_description(cls, meta):
        return meta.findtext(NS.PyWebXML.description)

    def parse_tree(self, root, header_offset=1):
        """
        Take the root element of an ElementTree and interpret it as PyWebXML
        document. Return the resulting :class:`~PyXWF.Document.Document`
        instance on success and raise on error.

        *header_offset* works as documented in the base class'
        :meth:`~PyXWF.Parsers.ParserBase.transform_headers` method.
        """
        if root.tag != NS.PyWebXML.page:
            raise ValueError("This is not a pyxwf-xml document.")

        meta = root.find(NS.PyWebXML.meta)
        if meta is None:
            raise ValueError("Metadata is missing.")

        title = unicode(meta.findtext(NS.PyWebXML.title))
        if title is None:
            raise ValueError("Title is missing.")

        keywords = self.get_keywords(meta)
        links = self.get_links(meta)

        body = root.find(NS.XHTML.body)
        if body is None:
            raise ValueError("No body tag found")
        self.transform_headers(body, header_offset)

        date = self.get_date(meta)
        authors = self.get_authors(meta)
        hmeta = self.get_meta(meta)
        description = self.get_description(meta)

        ext = meta

        return Document.Document(title, keywords, links, body,
            ext=ext, date=date, authors=authors, hmeta=hmeta,
            description=description)

    def parse(self, fileref, **kwargs):
        """
        Parse the file referenced by *fileref* as PyWebXML document and return
        the resulting :class:`~PyXWF.Document.Document` instance.
        """
        tree = ET.parse(fileref)
        root = tree.getroot()
        return self.parse_tree(root, **kwargs)
