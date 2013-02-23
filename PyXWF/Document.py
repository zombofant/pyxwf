# File name: Document.py
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
import abc
import os
import mimetypes
import copy
from datetime import datetime

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Resource as Resource
import PyXWF.Errors as Errors
import PyXWF.Registry as Registry
import PyXWF.Cache as Cache

class Author(object):
    @classmethod
    def from_node(cls, node):
        fullname = unicode(node.text)
        email = node.get("email")
        pagehref = node.get("href")
        return cls(fullname, email, pagehref, id=node.get("id"))

    def __init__(self, fullname, email, pagehref, id=None):
        super(Author, self).__init__()
        self.fullname = fullname
        self.email = email
        self.pagehref = pagehref
        self.id = id

    def apply_to_node(self, node, carryid=True):
        if self.id and carryid:
            node.set("id", self.id)
        if self.pagehref:
            node.set("href", self.pagehref)
        if self.email:
            node.set("email", self.email)
        node.text = self.fullname

    def to_node(self):
        node = ET.Element(NS.PyWebXML.author)
        self.apply_to_node(node)
        return node


class License(object):
    @classmethod
    def from_node(cls, node):
        intohref = node.get("href")
        imghref = node.get("img-href")
        description = node.text
        name = node.get("name")
        return cls(name, description, intohref, imghref)

    def __init__(self, name, description, intohref, imghref):
        super(License, self).__init__()
        self.name = name
        self.description = description
        self.intohref = intohref
        self.imghref = imghref

    def apply_to_node(self, node):
        if self.name:
            node.set("name", self.name)
        if self.description:
            node.text = self.description
        if self.intohref:
            node.set("href", self.intohref)
        if self.imghref:
            node.set("img-href", self.imghref)

    def to_node(self):
        node = ET.Element(NS.PyWebXML.license)
        self.apply_to_node(node)
        return node


class Document(Cache.Cachable):
    """
    Contains all relevant information about a Document. *body* must be a valid
    xhtml body (as :mod:`lxml.etree` nodes). *title* must be a string-like
    containing the title which is used on the page. *keywords* must be an
    iterable of strings and *links* must be an iterable of etree nodes
    which resemble nodes to put into the xhtml header. These are used for
    stylesheet and script associations, but can also contain different elements.

    *last_modified* is optionally a :class:`datetime.datetime` object representing
    the last modification date of the document. Can be *None* if unknown or not
    well defined and to prevent caching.

    *etag* is a short string like specified in
    `RFC 2616, Section 14.19 <https://tools.ietf.org/html/rfc2616#section-14.19>`_.
    Can be *None* to prevent caching.

    *ext* can be a element tree node which contains all nodes with foreign
    namespaces which could not be interpreted by the document parser.
    """

    def __init__(self, title, keywords, links, body,
            etag=None,
            ext=None,
            authors=None,
            date=None,
            license=None,
            hmeta=None,
            description=None):
        super(Document, self).__init__()
        self.title = title
        self.authors = list(authors or [])
        self.keywords = keywords
        self.links = links
        self.hmeta = list(hmeta or [])
        self.body = body
        self.etag = etag
        self.date = date
        self.description = description
        self.license = license
        self.ext = ET.Element("blank") if ext is None else ext

    def to_PyWebXML_page(self):
        """
        Wrap the documents body in an element tree which represents the document
        as PyWebXML page. Return the pywebxml page root node.
        """
        page = ET.Element(NS.PyWebXML.page)
        meta = ET.SubElement(page, NS.PyWebXML.meta)

        title = ET.SubElement(meta, NS.PyWebXML.title)
        title.text = self.title

        for author in self.authors:
            meta.append(author.to_node())

        for keyword in self.keywords:
            kw = ET.SubElement(meta, NS.PyWebXML.kw)
            kw.text = keyword

        for link in self.links:
            meta.append(copy.deepcopy(link))

        for hmeta in self.hmeta:
            meta.append(copy.deepcopy(hmeta))

        for ext in self.ext:
            meta.append(copy.deepcopy(ext))

        if self.date:
            date = ET.SubElement(meta, NS.PyWebXML.date)
            date.text = self.date.isoformat() + "Z"

        if self.license:
            meta.append(self.license.to_node())

        if self.description:
            ET.SubElement(meta, NS.PyWebXML.description).text = self.description

        page.append(copy.deepcopy(self.body))

        return page

    def get_template_arguments(self):
        return {
            b"doc_title": utils.unicode2xpathstr(self.title)
        }

class DocumentResource(Resource.Resource):
    pass

class FileDocument(DocumentResource):
    """
    Load and hold the document referred to by *filename* (optionally with a
    fixed MIME type *override_mime*) in a cachable fashion. Provides the document
    as *doc* attribute.
    """
    def __init__(self, site, filename, override_mime=None, **kwargs):
        super(FileDocument, self).__init__()
        self._last_modified = utils.file_last_modified(filename)
        self._filename = filename
        mimetype = override_mime
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename, strict=False)
            if mimetype is None:
                raise Errors.UnknownMIMEType(filename)
        self._kwargs = kwargs
        self._parser = site.parser_registry[mimetype]
        self._reload()

    def _reload(self):
        self.doc = self._parser.parse(self._filename, **self._kwargs)

    @property
    def LastModified(self):
        return self._last_modified

    def update(self):
        last_modified = utils.file_last_modified(self._filename)
        if last_modified is None:
            raise Errors.ResourceLost(self._filename)
        if self._last_modified < last_modified:
            self._last_modified = last_modified
            self._reload()


class FileDocumentCache(Cache.FileSourcedCache):
    """
    A sub class of a :class:`~PyXWF.Cache.FileSourcedCache` which keeps
    :class:`~FileDocument` instances.
    """

    def _load(self, path, override_mime=None, **kwargs):
        return FileDocument(self.site, path, override_mime=override_mime, **kwargs)

    def get(self, key, override_mime=None, **kwargs):
        return super(FileDocumentCache, self).__getitem__(key,
                override_mime=override_mime, **kwargs)
