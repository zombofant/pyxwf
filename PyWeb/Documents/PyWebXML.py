from PyWeb.utils import ET

import PyWeb.Registry as Registry
import PyWeb.Document as Document
import PyWeb.Namespaces as NS

class PyWebXML(Document.DocumentBase):
    __metaclass__ = Registry.DocumentMeta

    mimeTypes = ["application/x-pyweb-xml"]
    
    def __init__(self, mime):
        super(PyWebXML, self).__init__()

    @staticmethod
    def _linkFromNode(node):
        return Document.Link.create(
            node.get("rel"), node.get("type"), node.get("href")
        )

    @classmethod
    def getLinksAndKeywords(cls, meta):
        keywords = list(map(lambda node: unicode(node.text), meta.findall(NS.PyWebXML.kw)))
        links = list(map(cls._linkFromNode, meta.findall(NS.PyWebXML.link)))
        return keywords, links

    def parse(self, filelike):
        tree = ET.parse(filelike)
        root = tree.getroot()
        if root.tag != NS.PyWebXML.page:
            raise ValueError("This is not a pyweb-xml document.")

        meta = root.find(NS.PyWebXML.meta)
        if meta is None:
            raise ValueError("Metadata is missing.")

        title = unicode(meta.findtext(NS.PyWebXML.title))
        if title is None:
            raise ValueError("Title is missing.")

        keywords, links = self.getLinksAndKeywords(meta)

        body = root.find(NS.XHTML.body)
        if body is None:
            raise ValueError("No body tag found")

        return Document.Document(title, keywords, links, body)
