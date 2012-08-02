# encoding=utf-8
from __future__ import unicode_literals

import itertools
from datetime import datetime

import markdown2

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Parsers as Parsers
import PyWeb.Document as Document
import PyWeb.Namespaces as NS
import PyWeb.Types as Types

class _NS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/documents/markdown"

class Markdown(Parsers.ParserBase):
    __metaclass__ = Registry.ParserMeta

    namespace = str(_NS)
    tweakNames = ["tweaks", "nsdecl"]
    mimeTypes = ["text/x-markdown"]

    _allowHtmlType = Types.DefaultForNone(False, Types.Typecasts.bool)
    _prefixType = Types.Typecasts.unicode
    _xmlnsType = Types.Typecasts.unicode

    _template = """<?xml version="1.0" ?>
<body xmlns="{0}">{{0}}</body>""".format(NS.XHTML)

    def __init__(self, mime):
        self.NS = _NS
        super(Markdown, self).__init__()
        tweaks = self._tweaks["tweaks"].find(self.NS.tweaks)
        if tweaks is None:
            tweaks = ET.Element(self.NS.tweaks)

        if not self._allowHtmlType(tweaks.get("allow-html")):
            safe_mode = "escape"
        else:
            safe_mode = "false"
        self.md = markdown2.Markdown(
            extras=["metadata"],
            safe_mode=safe_mode
        )

        self._namespaces = {}
        for nsdecl in self._tweaks["nsdecl"].findall(self.NS.nsdecl):
            prefix = self._prefixType(nsdecl.get("prefix"))
            xmlns = self._xmlnsType(nsdecl.get("ns"))
            self._namespaces[prefix] = xmlns

    def transformHeaders(self, body):
        headers = reversed(xrange(1,7))
        matches = (getattr(NS.XHTML, "h{0}".format(i)) for i in headers)
        iterator = itertools.chain(*itertools.imap(body.iter, matches))
        for hX in iterator:
            i = int(hX.tag[-1:])
            i += 1
            hX.tag = getattr(NS.XHTML, "h"+str(i))

    def transformUrls(self, body):
        for a in body.iter(NS.XHTML.a):
            a.tag = NS.PyWebXML.a

        for img in body.iter(NS.XHTML.img):
            img.tag = NS.PyWebXML.img
            img.set("href", img.get("src"))
            del img.attrib["src"]

    def _authorFromId(self, id):
        return Document.Author(None, None, None, id=id)

    def _smartSplit(self, s):
        if "," in s:
            items = filter(lambda x: bool(x),
                    (item.strip() for item in s.split(",")))
        else:
            items = filter(lambda x: bool(x),
                    (item.strip() for item in s.split()))
        return items
        
    def parse(self, fileref):
        if isinstance(fileref, basestring):
            f = open(fileref, "r")
        else:
            f = fileref
        source = f.read()
        f.close()

        converted = self.md.convert(source)
        metadata = converted.metadata
        
        html = self._template.format(converted)
        body = ET.XML(html)
        self.transformHeaders(body)
        self.transformUrls(body)
        
        title = metadata.get("Title", None)
        date = utils.parseISODate(metadata.get("Date", None))
        authors = metadata.get("Authors", None)
        if authors is not None:
            authors = map(self._authorFromId, self._smartSplit(authors))
        keywords = self._smartSplit(metadata.get("Keywords", ""))

        ext = ET.Element(self.NS.ext)
        for key, value in metadata.viewitems():
            prefix, _, tag = key.partition("-")
            if len(_) == 0:
                continue
            try:
                ns = self._namespaces[prefix]
            except KeyError as err:
                raise ValueError("Unknown namespace prefix: {0}".format(err))
            node = ET.SubElement(ext, "{{{0}}}{1}".format(ns, tag))
            node.text = value

        return Document.Document(title, keywords, [], body,
            authors=authors, ext=ext, date=date)
