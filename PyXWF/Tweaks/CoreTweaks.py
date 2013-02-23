# File name: CoreTweaks.py
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
from __future__ import print_function, unicode_literals, absolute_import

import logging
import mimetypes
import os

import PyXWF
import PyXWF.Tweaks as Tweaks
import PyXWF.Namespaces as NS
import PyXWF.Types as Types
import PyXWF.Registry as Registry
from PyXWF.utils import _F

logging = logging.getLogger(__name__)

class CoreTweaks(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(NS.Site)

    def __init__(self, site):
        super(CoreTweaks, self).__init__(
            site,
            tweak_ns=self.namespace,
            tweak_hooks=[
                ("performance", self.tweak_performance),
                ("compatibility", self.tweak_compatibility),
                ("formatting", self.tweak_formatting),
                ("templates", self.tweak_templates),
                ("mime-map", self.tweak_mimemap),
                ("xml-namespaces", self.tweak_xml_namespaces)
            ]
        )
        site.pretty_print = False
        site.cache.Limit = 0
        site.html4_transform = os.path.join(PyXWF.data_path, "xsl", "tohtml4.xsl")
        site.long_date_format = "%c"
        site.short_date_format = "%c"
        site.not_found_template = "templates/errors/not-found.xsl"
        site.default_template = None
        mimetypes.init()
        site.xml_namespaces = {}
        site.force_namespaces = set()
        site.html_transforms = []
        site.disable_xhtml = False
        site.remove_xhtml_prefixes = False
        site.client_cache = True

    @classmethod
    def parse_tweak(cls, node, attribs, defaults={}):
        if isinstance(attribs, dict):
            known = set(attribs.keys())
            typecasts = attribs
        else:
            known = set(attribs)
            typecasts = {}
        result = {}
        result.update(defaults)
        for attrib, value in node.attrib.items():
            if attrib not in known:
                logging.warning(_F("Encountered unknown tweak attribute: {0}/@{1}", node.tag, attrib))
                continue
            result[attrib] = typecasts.get(attrib, lambda x: x)(value)
        return result

    def tweak_performance(self, node):
        results = self.parse_tweak(
            node,
            {
                "cache-limit": Types.NumericRange(int, 0, None),
                "pretty-print": Types.Typecasts.bool,
                "client-cache": Types.Typecasts.bool
            }
        )
        self.site.pretty_print = results.get("pretty-print", self.site.pretty_print)
        self.site.cache.Limit = results.get("cache-limit", self.site.cache.Limit)
        self.site.client_cache = results.get("client-cache", self.site.client_cache)

    def tweak_compatibility(self, node):
        results = self.parse_tweak(
            node,
            [
                "html4-transform",
                "disable-xhtml",
                "remove-xhtml-prefixes"
            ],
        )
        self.site.html4_transform = results.get("html4-transform", self.site.html4_transform)
        self.site.disable_xhtml = Types.Typecasts.bool(results.get("disable-xhtml", self.site.disable_xhtml))
        self.site.remove_xhtml_prefixes = Types.Typecasts.bool(results.get("remove-xhtml-prefixes", self.site.remove_xhtml_prefixes))

    def tweak_formatting(self, node):
        results = self.parse_tweak(
            node,
            [
                "date-format",
                "long-date-format",
                "short-date-format"
            ]
        )
        long_date = results.get("date-format", None)
        short_date = results.get("date-format", None)
        long_date = results.get("long-date-format", long_date)
        short_date = results.get("short-date-format", short_date)
        self.site.long_date_format = long_date or self.site.long_date_format
        self.site.short_date_format = short_date or self.site.short_date_format

    def tweak_templates(self, node):
        results = self.parse_tweak(
            node,
            [
                "not-found",
                "default"
            ]
        )
        self.site.not_found_template = results.get("not-found", self.site.not_found_template)
        self.site.default_template = results.get("default", self.site.default_template)

    def tweak_mimemap(self, node):
        for child in node.findall(NS.Site.mm):
            ext = Types.Typecasts.unicode(child.get("ext"))
            mime = Types.Typecasts.unicode(child.get("type"))
            mimetypes.add_type(mime, ext)

    def tweak_xml_namespaces(self, node):
        site = self.site
        for ns in node.findall(NS.Site.ns):
            prefix = ns.get("prefix")
            uri = Types.NotNone(ns.get("uri"))
            force = Types.Typecasts.bool(ns.get("force", False))
            # site.xml_namespacemap[prefix] = uri
            if force:
                site.force_namespaces.add((prefix, uri))

    def tweak_html_transform(self, node):
        results = self.parse_tweak(
            node,
            {
                "transform": Types.NotNone
            }
        )
        self.site.html_transforms.append(results["transform"])
