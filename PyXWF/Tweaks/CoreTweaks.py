from __future__ import print_function, unicode_literals, absolute_import

import logging
import mimetypes
import os

import PyXWF
import PyXWF.Tweaks as Tweaks
import PyXWF.Namespaces as NS
import PyXWF.Types as Types
import PyXWF.Registry as Registry

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
                logging.log("Encountered unknown tweak attribute: {0}/@{1}".format(node.tag, attrib))
                continue
            result[attrib] = typecasts.get(attrib, lambda x: x)(value)
        return result

    def tweak_performance(self, node):
        results = self.parse_tweak(
            node,
            {
                "cache-limit": Types.NumericRange(int, 0, None),
                "pretty-print": Types.Typecasts.bool
            }
        )
        self.site.pretty_print = results.get("pretty-print", self.site.pretty_print)
        self.site.cache.Limit = results.get("cache-limit", self.site.cache.Limit)

    def tweak_compatibility(self, node):
        results = self.parse_tweak(
            node,
            ["html4-transform"],
        )
        self.site.html4_transform = results.get("html4-transform", self.site.html4_transform)

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
