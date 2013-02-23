# encoding=utf-8
# File name: PyWebXML.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
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
    _known_nodes = {
        NS.XHTML.meta,
        NS.PyWebXML.title,
        NS.PyWebXML.link,
        NS.PyWebXML.author,
        NS.PyWebXML.date,
        NS.PyWebXML.description,
        NS.PyWebXML.kw,
        NS.PyWebXML.script,
    }

    def __init__(self, site):
        super(PyWebXML, self).__init__(site,
            parser_mimetypes=self.mimetypes
        )

    def _link_from_node(self, node):
        return node

    def _is_ext_node(self, node):
        return node.tag is not ET.Comment and node.tag not in self._known_nodes

    def get_links(self, meta):
        return list(map(self._link_from_node, itertools.chain(
            meta.findall(NS.PyWebXML.link),
            meta.findall(NS.PyWebXML.script)
        )))

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

        ext = [node for node in meta if self._is_ext_node(node)]

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
