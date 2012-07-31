import abc

from PyWeb.utils import ET
import PyWeb.Namespaces as NS

class DocumentBase(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        pass

    @abc.abstractmethod
    def parse(self, filelike):
        pass

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

class Document(object):
    def __init__(self, title, keywords, links, body):
        super(Document, self).__init__()
        self.title = title
        self.keywords = keywords
        self.links = links
        self.body = body
