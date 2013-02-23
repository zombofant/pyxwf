# encoding=utf-8
# File name: Markdown.py
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
from __future__ import unicode_literals

import itertools
from datetime import datetime

import markdown2

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Registry as Registry
import PyXWF.Parsers as Parsers
import PyXWF.Document as Document
import PyXWF.Namespaces as NS
import PyXWF.Types as Types
import PyXWF.Tweaks as Tweaks

class MarkdownNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/documents/markdown"

class Markdown(Parsers.ParserBase, Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(MarkdownNS)
    mimetypes = ["text/x-markdown"]

    _allow_html_type = Types.DefaultForNone(False, Types.Typecasts.bool)
    _prefix_type = Types.Typecasts.unicode
    _xmlns_type = Types.Typecasts.unicode

    _template = """<?xml version="1.0" ?>
<body xmlns="{0}">{{0}}</body>""".format(NS.XHTML)

    def __init__(self, site):
        super(Markdown, self).__init__(site,
            tweak_ns=self.namespace,
            tweak_hooks=[("tweaks", self.tweak), ("nsdecl", self.nsdecl)],
            parser_mimetypes=self.mimetypes
        )
        self.md = markdown2.Markdown(
            extras=["metadata"],
            safe_mode="escape"
        )
        self._namespaces = {}

    def tweak(self, tweak):
        kwargs = {}
        extras = ["metadata"]
        if not self._allow_html_type(tweak.get("allow-html")):
            kwargs["safe_mode"] = "escape"

        if Types.Typecasts.bool(tweak.get("smarty-pants", True)):
            extras.append("smarty-pants")

        self.md = markdown2.Markdown(
            extras=extras,
            **kwargs
        )

    def nsdecl(self, nsdecl):
        prefix = self._prefix_type(nsdecl.get("prefix"))
        xmlns = self._xmlns_type(nsdecl.get("uri"))
        self._namespaces[prefix] = xmlns

    def transform_urls(self, body):
        for a in body.iter(NS.XHTML.a):
            a.tag = NS.PyWebXML.a

        for img in body.iter(NS.XHTML.img):
            img.tag = NS.PyWebXML.img
            img.set("href", img.get("src"))
            del img.attrib["src"]

    def transform_images(self, body):
        ptag, imgtag, atag = NS.XHTML.p, NS.XHTML.img, NS.XHTML.a
        for p in body.iter(ptag):
            if len(p) != 1:
                continue
            a_or_img = p[0]
            if a_or_img.tag == imgtag:
                p.set("class", "imgbox")
                continue
            if a_or_img.tag != atag:
                continue
            a = a_or_img
            if len(a) != 1:
                continue
            img = a[0]
            if img.tag == imgtag:
                p.set("class", "imgbox")
                p.tag = NS.XHTML.div

    def _author_from_id(self, id):
        return Document.Author(None, None, None, id=id)

    def _smart_split(self, s):
        if "," in s:
            items = filter(lambda x: bool(x),
                    (item.strip() for item in s.split(",")))
        else:
            items = filter(lambda x: bool(x),
                    (item.strip() for item in s.split()))
        return items

    def parse(self, fileref, header_offset=1):
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
        self.transform_headers(body, header_offset)
        self.transform_images(body)
        self.transform_urls(body)

        title = metadata.get("Title", None)
        date = utils.parse_iso_date(metadata.get("Date", None))
        authors = metadata.get("Authors", None)
        description = metadata.get("Description", None)
        if authors is not None:
            authors = map(self._author_from_id, self._smart_split(authors))
        keywords = self._smart_split(metadata.get("Keywords", ""))

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
            authors=authors, ext=ext, date=date, description=description)
