import abc, os, mimetypes
from datetime import datetime

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Resource as Resource
import PyWeb.Errors as Errors
import PyWeb.Registry as Registry
import PyWeb.Cache as Cache

class Author(object):
    @classmethod
    def fromNode(cls, node):
        fullName = unicode(node.text)
        eMail = node.get("email")
        pageHref = node.get("href")
        return cls(fullName, eMail, pageHref, id=node.get("id"))

    def __init__(self, fullName, eMail, pageHref, id=None):
        super(Author, self).__init__()
        self.fullName = fullName
        self.eMail = eMail
        self.pageHref = pageHref
        self.id = id

    def applyToNode(self, node, carryID=True):
        if self.id and carryID:
            node.set("id", self.id)
        if self.pageHref:
            node.set("href", self.pageHref)
        if self.eMail:
            node.set("email", self.eMail)
        node.text = self.fullName

    def toNode(self):
        node = ET.Element(NS.PyWebXML.author)
        self.applyToNode(node)
        return node


class License(object):
    @classmethod
    def fromNode(cls, node):
        infoHref = node.get("href")
        imgHref = node.get("img-href")
        description = node.text
        name = node.get("name")
        return cls(name, description, infoHref, imgHref)

    def __init__(self, name, description, infoHref, imgHref):
        super(License, self).__init__()
        self.name = name
        self.description = description
        self.infoHref = infoHref
        self.imgHref = imgHref

    def applyToNode(self, node):
        if self.name:
            node.set("name", self.name)
        if self.description:
            node.text = self.description
        if self.infoHref:
            node.set("href", self.infoHref)
        if self.imgHref:
            node.set("img-href", self.imgHref)

    def toNode(self):
        node = ET.Element(NS.PyWebXML.license)
        self.applyToNode(node)
        return node


class Document(object):
    """
    Contains all relevant information about a Document. *body* must be a valid
    xhtml body (as :mod:`lxml.etree` nodes). *title* must be a string-like
    containing the title which is used on the page. *keywords* must be an
    iterable of strings and *links* must be an iterable of etree nodes
    which resemble nodes to put into the xhtml header. These are used for
    stylesheet and script associations, but can also contain different elements.

    *lastModified* is optionally a :cls:`datetime.datetime` object representing
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
            hmeta=None):
        super(Document, self).__init__()
        self.title = title
        self.authors = list(authors or [])
        self.keywords = keywords
        self.links = links
        self.hmeta = list(hmeta or [])
        self.body = body
        self.etag = etag
        self.date = date
        self.license = license
        self.ext = ET.Element("blank") if ext is None else ext

    def toPyWebXMLPage(self):
        """
        Wrap the documents body in an element tree which represents the document
        as PyWebXML page. Return the pywebxml page root node.
        """
        page = ET.Element(NS.PyWebXML.page)
        meta = ET.SubElement(page, NS.PyWebXML.meta)

        title = ET.SubElement(meta, NS.PyWebXML.title)
        title.text = self.title

        for author in self.authors:
            meta.append(author.toNode())

        for keyword in self.keywords:
            kw = ET.SubElement(meta, NS.PyWebXML.kw)
            kw.text = keyword

        for link in self.links:
            meta.append(link)

        for hmeta in self.hmeta:
            meta.append(hmeta)

        if self.date:
            date = ET.SubElement(meta, NS.PyWebXML.date)
            date.text = self.date.isoformat() + "Z"

        if self.license:
            meta.append(self.license.toNode())

        page.append(self.body)

        return page

    def getTemplateArguments(self):
        return {
            b"doc_title": utils.unicodeToXPathStr(self.title)
        }


class DocumentResource(Resource.Resource):
    pass


class FileDocument(DocumentResource):
    """
    Load and hold the document referred to by *fileName* (optionally with a
    fixed MIME type *overrideMIME*) in a cachable fashion. Provides the document
    as *doc* attribute.
    """
    def __init__(self, fileName, overrideMIME=None, **kwargs):
        super(FileDocument, self).__init__()
        self._lastModified = utils.fileLastModified(fileName)
        self._fileName = fileName
        mimeType = overrideMIME
        if mimeType is None:
            mimeType, _ = mimetypes.guess_type(fileName, strict=False)
            if mimeType is None:
                raise Errors.UnknownMIMEType(fileName)
        self._kwargs = kwargs
        self._parser = Registry.ParserPlugins(mimeType)
        self._reload()

    def _reload(self):
        self.doc = self._parser.parse(self._fileName, **self._kwargs)

    @property
    def LastModified(self):
        return self._lastModified

    def update(self):
        lastModified = utils.fileLastModified(self._fileName)
        if lastModified is None:
            raise Errors.ResourceLost(self._fileName)
        if self._lastModified < lastModified:
            self._lastModified = lastModified
            self._reload()


class FileDocumentCache(Cache.FileSourcedCache):
    """
    A sub class of a :cls:`Cache.FileSourcedCache` which keeps
    :cls:`FileDocument` instances.
    """

    def _load(self, path, overrideMIME=None, **kwargs):
        return FileDocument(path, overrideMIME=overrideMIME, **kwargs)

    def get(self, key, overrideMIME=None, **kwargs):
        return super(FileDocumentCache, self).__getitem__(key,
                overrideMIME=overrideMIME, **kwargs)
