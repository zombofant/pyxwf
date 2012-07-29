import abc
import xml.etree.ElementTree as ET

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
    
    @staticmethod
    def create(rel, typeName, href):
        if rel == "stylesheet":
            return ET.Element(self._linkTag, attrib={
                "rel": "stylesheet",
                "type": typeName,
                "href": href
            })
        elif rel == "script":
            return ET.Element(self._scriptTag, attrib={
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
