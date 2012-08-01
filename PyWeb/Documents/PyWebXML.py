from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Document as Document
import PyWeb.Namespaces as NS

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


class PyWebXML(Document.DocumentBase):
    __metaclass__ = Registry.DocumentMeta

    mimeTypes = ["application/x-pyweb-xml"]
    
    def __init__(self, mime):
        super(PyWebXML, self).__init__()

    @staticmethod
    def _linkFromNode(node):
        return Link.create(
            node.get("rel"), node.get("type"), node.get("href"), node.get("media")
        )

    @classmethod
    def getKeywordsAndLinks(cls, meta):
        keywords = list(map(lambda node: unicode(node.text), meta.findall(NS.PyWebXML.kw)))
        links = list(map(cls._linkFromNode, meta.findall(NS.PyWebXML.link)))
        return keywords, links

    def parse(self, fileref):
        lastModified = utils.fileLastModified(fileref)
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

        ext = meta
        
        return Document.Document(title, keywords, links, body,
            lastModified=lastModified, ext=ext)
