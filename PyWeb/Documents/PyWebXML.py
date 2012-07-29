from PyWeb.utils import ET

import PyWeb.Registry as Registry
import PyWeb.Document as Document
import PyWeb.Namespaces as NS

class PyWebXML(Document.DocumentBase):
    __metaclass__ = Registry.DocumentMeta

    mimeTypes = ["application/x-pyweb-xml"]
    namespace = NS.PyWebXML
    xhtmlNamespace = NS.xhtml

    _pageTag = "{{{0}}}page".format(namespace)
    _metaTag = "{{{0}}}meta".format(namespace)
    _titleTag = "{{{0}}}title".format(namespace)
    _keywordTag = "{{{0}}}kw".format(namespace)
    _linkTag = "{{{0}}}link".format(namespace)
    _bodyTag = "{{{0}}}body".format(xhtmlNamespace)
    
    def __init__(self, mime):
        super(PyWebXML, self).__init__()

    @staticmethod
    def _linkFromNode(node):
        return Document.Link.create(
            node.get("rel"), node.get("type"), node.get("href")
        )

    @classmethod
    def getLinksAndKeywords(cls, meta):
        keywords = list(map(lambda node: unicode(node.text), meta.findall(cls._keywordTag)))
        links = list(map(cls._linkFromNode, meta.findall(cls._linkTag)))
        return keywords, links

    def parse(self, filelike):
        tree = ET.parse(filelike)
        root = tree.getroot()
        if root.tag != self._pageTag:
            raise ValueError("This is not a pyweb-xml document.")

        meta = root.find(self._metaTag)
        if meta is None:
            raise ValueError("Metadata is missing.")

        title = unicode(meta.findtext(self._titleTag))
        if title is None:
            raise ValueError("Title is missing.")

        keywords, links = self.getLinksAndKeywords(meta)

        body = root.find(self._bodyTag)
        if body is None:
            raise ValueError("No body tag found")

        return Document.Document(title, keywords, links, body)
