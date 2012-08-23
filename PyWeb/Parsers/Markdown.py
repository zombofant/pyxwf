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
import PyWeb.Tweaks as Tweaks

class MarkdownNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/documents/markdown"

class Markdown(Parsers.ParserBase, Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(MarkdownNS)
    mimeTypes = ["text/x-markdown"]

    _allowHtmlType = Types.DefaultForNone(False, Types.Typecasts.bool)
    _prefixType = Types.Typecasts.unicode
    _xmlnsType = Types.Typecasts.unicode

    _template = """<?xml version="1.0" ?>
<body xmlns="{0}">{{0}}</body>""".format(NS.XHTML)

    def __init__(self, site):
        super(Markdown, self).__init__(site,
            tweakNS=self.namespace,
            tweakHooks=[("tweaks", self.tweak), ("nsdecl", self.nsdecl)],
            parserMimeTypes=self.mimeTypes
        )
        self.md = markdown2.Markdown(
            extras=["metadata"],
            safe_mode="escape"
        )
        self._namespaces = {}

    def tweak(self, tweak):
        kwargs = {}
        if not self._allowHtmlType(tweak.get("allow-html")):
            kwargs["safe_mode"] = "escape"

        self.md = markdown2.Markdown(
            extras=["metadata"],
            **kwargs
        )

    def nsdecl(self, nsdecl):
        prefix = self._prefixType(nsdecl.get("prefix"))
        xmlns = self._xmlnsType(nsdecl.get("uri"))
        self._namespaces[prefix] = xmlns

    def transformUrls(self, body):
        for a in body.iter(NS.XHTML.a):
            a.tag = NS.PyWebXML.a

        for img in body.iter(NS.XHTML.img):
            img.tag = NS.PyWebXML.img
            img.set("href", img.get("src"))
            del img.attrib["src"]

    def transformImages(self, body):
        pTag, imgTag, aTag = NS.XHTML.p, NS.XHTML.img, NS.XHTML.a
        for p in body.iter(pTag):
            if len(p) != 1:
                continue
            aOrImg = p[0]
            if aOrImg.tag == imgTag:
                p.set("class", "imgbox")
                continue
            if aOrImg.tag != aTag:
                continue
            a = aOrImg
            if len(a) != 1:
                continue
            img = a[0]
            if img.tag == imgTag:
                p.set("class", "imgbox")
                p.tag = NS.XHTML.div

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

    def parse(self, fileref, headerOffset=1):
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
        self.transformHeaders(body, headerOffset)
        self.transformImages(body)
        self.transformUrls(body)

        title = metadata.get("Title", None)
        date = utils.parseISODate(metadata.get("Date", None))
        authors = metadata.get("Authors", None)
        if authors is not None:
            authors = map(self._authorFromId, self._smartSplit(authors))
        keywords = self._smartSplit(metadata.get("Keywords", ""))

        ext = ET.Element(MarkdownNS.ext)
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
