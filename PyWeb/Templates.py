"""
A basic XSLT template implementation.
"""

import abc, itertools, os, copy

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Resource as Resource
import PyWeb.Cache as Cache
import PyWeb.Namespaces as NS
import PyWeb.Document as Document
import PyWeb.Parsers.PyWebXML as PyWebXML

class Template(Resource.Resource):
    """
    Baseclass for templating, which is not bound to XSLT yet. It provides some
    shared mechanims, like being file-bound and a finalization method which
    does the final transformation (including PyWeb specific transformations
    which are provided by the Site object).
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, fileName):
        super(Template, self).__init__()
        self.fileName = fileName
        self._lastModified = utils.fileLastModified(fileName)

    @property
    def LastModified(self):
        return self._lastModified

    @abc.abstractmethod
    def transform(self, body, templateArgs):
        pass

    def final(self, site, ctx, document, licenseFallback=None):
        """
        Do the final transformation on *document*. This includes adding
        keywords and author information, setting up the title, loading crumbs,
        replacing local links and more.
        """
        templateArgs = site.getTemplateArguments()
        templateArgs.update(document.getTemplateArguments())

        metaPath = NS.PyWebXML.meta
        licensePath = metaPath + "/" + NS.PyWebXML.license
        page = document.toPyWebXMLPage()
        if licenseFallback is not None and page.find(licensePath) is None:
            page.find(metaPath).append(licenseFallback.toNode())
        site.transformReferences(ctx, page)

        newDoc = self.transform(page, templateArgs)
        newDoc.title = newDoc.title or document.title
        body = newDoc.body

        if body is None:
            raise ValueError("Transform did not return a valid body.")


        html = ET.Element(NS.XHTML.html)
        head = ET.SubElement(html, NS.XHTML.head)
        ET.SubElement(head, NS.XHTML.title).text = \
                newDoc.title or document.title
        for link in newDoc.links:
            ieLimit = link.get("ie-only")
            if ieLimit is not None:
                link = copy.copy(link)
                site.transformHref(link)
                link.tag = "link"
                ET.cleanup_namespaces(link)
                del link.attrib["ie-only"]
                s = ET.tostring(link, method="html", xml_declaration="no", encoding="utf-8").decode("utf-8")
                s = "[{0}]>{1}<![endif]".format(ieLimit, s)
                link = ET.Comment()
                link.text = s
                link.tail = "\n"
            head.append(link)
        if len(newDoc.keywords) > 0:
            ET.SubElement(head, NS.XHTML.meta, attrib={
                "name": "keywords",
                "content": ",".join(newDoc.keywords)
            })
        html.append(body)
        site.transformPyNamespace(ctx, html)

        return ET.ElementTree(html)


class XSLTTemplate(Template):
    """
    A specific templating implementation which uses XSLT as backend.
    """
    def __init__(self, fileName):
        super(XSLTTemplate, self).__init__(fileName)
        self._parseTemplate()

    def update(self):
        self._lastModified = utils.fileLastModified(self.fileName)
        self._parseTemplate()

    def _parseTemplate(self):
        self.xsltTransform = ET.XSLT(ET.parse(self.fileName))

    def rawTransform(self, body, templateArgs):
        return self.xsltTransform(body, **templateArgs)

    def transform(self, body, templateArgs, customBody=NS.XHTML.body):
        newDoc = self.rawTransform(body, templateArgs)

        meta = newDoc.find(NS.PyWebXML.meta)
        if meta is not None:
            keywords, links = PyWebXML.PyWebXML.getKeywordsAndLinks(meta)
            title = meta.findtext(NS.PyWebXML.title)
        else:
            links, keywords = [], []
            title = None

        body = newDoc.find(customBody)
        return Document.Document(title, keywords, links, body)


class XSLTTemplateCache(Cache.FileSourcedCache):
    """
    A :cls:`Cache.FileSourcedCache` which is specialized for
    :cls:`XSLTTemplate` instances.
    """
    def _load(self, path):
        return XSLTTemplate(path)


