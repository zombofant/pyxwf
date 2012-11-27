"""
A basic XSLT template implementation.
"""

import abc
import itertools
import os
import copy
import logging

from PyXWF.utils import ET, _F
import PyXWF.utils as utils
import PyXWF.Resource as Resource
import PyXWF.Cache as Cache
import PyXWF.Namespaces as NS
import PyXWF.Document as Document
import PyXWF.Registry as Registry
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Parsers.PyWebXML as PyWebXML

logger = logging.getLogger(__name__)

class Template(Resource.Resource):
    """
    Baseclass for templating, which is not bound to XSLT yet. It provides some
    shared mechanims, like being file-bound and a finalization method which
    does the final transformation (including PyXWF specific transformations
    which are provided by the Site object).
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, site, filename):
        super(Template, self).__init__()
        self.site = site
        self.filename = filename
        self._last_modified = utils.file_last_modified(filename)

    @property
    def LastModified(self):
        return self._last_modified

    @abc.abstractmethod
    def transform(self, body, template_args={}):
        pass

    def final(self, ctx, document, license_fallback=None):
        """
        Do the final transformation on *document*. This includes adding
        keywords and author information, setting up the title, loading crumbs,
        replacing local links and more.
        """
        template_args = self.site.get_template_arguments(ctx)
        template_args.update(document.get_template_arguments())

        metapath = NS.PyWebXML.meta
        licensepath = metapath + "/" + NS.PyWebXML.license
        page = document.to_PyWebXML_page()
        if license_fallback is not None and page.find(licensepath) is None:
            page.find(metapath).append(license_fallback.to_node())
        self.site.transform_references(ctx, page)

        newdoc = self.transform(page, template_args)
        newdoc.title = newdoc.title or document.title
        body = newdoc.body

        if body is None:
            raise ValueError("Transform did not return a valid body.")

        html = ET.Element(NS.XHTML.html)
        head = ET.SubElement(html, NS.XHTML.head)
        ET.SubElement(head, NS.XHTML.title).text = \
                newdoc.title or document.title
        html_ns = unicode(NS.XHTML)
        for hmeta in newdoc.hmeta:
            head.append(hmeta)
        for helement in newdoc.ext:
            tag = helement.tag
            if not isinstance(tag, basestring):
                continue
            ns, name = utils.split_tag(tag)
            if ns == html_ns:
                head.append(helement)
        for link in newdoc.links:
            rel = link.get("rel")
            if rel == "script":
                link = ET.Element(NS.XHTML.script, attrib={
                    NS.LocalR.src: link.get("href"),
                    "type": link.get("type")
                })
            else:
                ielimit = link.get("ie-only")
                if ielimit is not None:
                    link = copy.copy(link)
                    self.site.transform_href(ctx, link)
                    link.tag = "link"
                    del link.attrib["ie-only"]
                    ET.cleanup_namespaces(link)
                    s = ET.tostring(link, method="html", xml_declaration="no", encoding="utf-8").decode("utf-8")
                    s = "[{0}]>{1}<![endif]".format(ielimit, s)
                    link = ET.Comment()
                    link.text = s
                    link.tail = "\n"
            head.append(link)
        if len(newdoc.keywords) > 0:
            ET.SubElement(head, NS.XHTML.meta, attrib={
                "name": "keywords",
                "content": ",".join(newdoc.keywords)
            })
        html.append(body)
        html = self.site.transform_py_namespace(ctx, html)

        return ET.ElementTree(html)


class XSLTTemplate(Template):
    """
    A specific templating implementation which uses XSLT as backend.
    """
    def __init__(self, site, filename):
        super(XSLTTemplate, self).__init__(site, filename)
        self._parse_template()

    def update(self):
        last_modified = utils.file_last_modified(self.filename)
        if last_modified > self._last_modified:
            self._last_modified = last_modified
            self._parse_template()

    def _parse_template(self):
        self.xslt_transform = ET.XSLT(ET.parse(self.filename))

    def raw_transform(self, body, template_args):
        return self.xslt_transform(body, **template_args)

    def transform(self, body, template_args={}, custom_body=NS.XHTML.body):
        newdoc = self.raw_transform(body, template_args)
        return self.site.parser_registry[ContentTypes.PyWebXML].parse_tree(newdoc.getroot(), header_offset=0)


class XSLTTemplateCache(Cache.FileSourcedCache):
    """
    A :class:`~PyXWF.Cache.FileSourcedCache` which is specialized for
    :class:`~XSLTTemplate` instances.
    """
    def _load(self, path):
        logger.debug(_F("requesting template at {0}", path))
        tpl = XSLTTemplate(self.site, path)
        logger.debug(_F("template at {0} loaded ok", path))
        return tpl
