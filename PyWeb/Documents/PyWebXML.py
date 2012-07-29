import xml.etree.ElementTree as ET

import PyWeb.Registry as Registry
import PyWeb.Document as Document
import PyWeb.Namespaces as NS

class PyWebXML(Document.DocumentBase):
    __metaclass__ = Registry.DocumentMeta

    mimeTypes = ["application/x-pyweb-xml"]
    namespace = "http://pyweb.sotecware.net/documents/pywebxml"
    xhtmlNamespace = NS.xhtml

    _pageTag = "{{{0}}}page".format(namespace)
    _metaTag = "{{{0}}}meta".format(namespace)
    _titleTag = "{{{0}}}title".format(namespace)
    _keywordTag = "{{{0}}}kw".format(namespace)
    _linkTag = "{{{0}}}link".format(namespace)
    _bodyTag = "{{{0}}}body".format(xhtmlNamespace)
    _localLinkTag = "{{{0}}}a".format(namespace)
    _aTag = "{{{0}}}a".format(xhtmlNamespace)
    
    def __init__(self, mime):
        super(PyWebXML, self).__init__()

    def parse(self, filelike):
        tree = ET.parse(filelike)
        root = tree.getroot()
        if root.tag != self._pageTag:
            raise ValueError("This is not a pyweb-xml document.")

        meta = root.find(self._metaTag)
        if meta is None:
            raise ValueError("Metadata is missing.")

        title = meta.findtext(self._titleTag)
        if title is None:
            raise ValueError("Title is missing.")

        keywords = list(map(lambda node: node.text, meta.findall(self._keywordTag)))
        links = list(map(lambda node: Document.Link.create(node.get("rel"), node.get("type"), node.get("href")), meta.findall(self._linkTag)))

        body = root.find(self._bodyTag)
        if body is None:
            raise ValueError("No body tag found")

        return Document.Document(title, keywords, links, body)
