import abc, itertools

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Cache as Cache
import PyWeb.Namespaces as NS
import PyWeb.Document as Document
import PyWeb.Documents.PyWebXML as PyWebXML

class Template(Cache.Cachable):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, fileName):
        super(Template, self).__init__()
        self.fileName = fileName
        self._lastModified = utils.fileLastModified(fileName)

    @property
    def LastModified(self):
        lastModified = utils.fileLastModified(self.fileName)
        if self._lastModified != lastModified:
            self._reload()
            self._lastModified = lastModified
        return self._lastModified

    @abc.abstractmethod
    def _reload(self):
        pass

    @abc.abstractmethod
    def transform(self, body, templateArgs):
        pass

    def final(self, site, ctx, document, licenseFallback=None):
        templateArgs = site.getTemplateArguments()
        templateArgs.update(document.getTemplateArguments())

        metaPath = NS.PyWebXML.meta
        licensePath = metaPath + "/" + NS.PyWebXML.license
        page = document.toPyWebXMLPage()
        if licenseFallback is not None and page.find(licensePath) is None:
            page.find(metaPath).append(licenseFallback.toNode())
        site.transformReferences(ctx, page)
        
        newDoc = self.transform(page, templateArgs)
        newDoc.links.extend(document.links)
        newDoc.keywords.extend(document.keywords)
        body = newDoc.body
        
        if body is None:
            raise ValueError("Transform did not return a valid body.")
        
        ctx.body = body
        site.transformPyNamespace(ctx, body)

        html = ET.Element(NS.XHTML.html)
        head = ET.SubElement(html, NS.XHTML.head)
        ET.SubElement(head, NS.XHTML.title).text = newDoc.title or document.title
        for link in newDoc.links:
            site.transformHref(link)
            head.append(link)
        if len(newDoc.keywords) > 0:
            ET.SubElement(head, NS.XHTML.meta, attrib={
                "name": "keywords",
                "content": " ".join(newDoc.keywords)
            })
        html.append(body)
        
        return ET.ElementTree(html)


class XSLTTemplate(Template):
    def __init__(self, fileName):
        super(XSLTTemplate, self).__init__(fileName)
        self._parseTemplate()

    def _reload(self):
        self._parseTemplate()

    def _parseTemplate(self):
        self.xsltTransform = ET.XSLT(ET.parse(self.fileName))

    def transform(self, body, templateArgs, customBody=NS.XHTML.body):
        newDoc = self.xsltTransform(body, **templateArgs)
        
        meta = newDoc.find(NS.PyWebXML.meta)
        if meta is not None:
            keywords, links = PyWebXML.PyWebXML.getKeywordsAndLinks(meta)
            title = unicode(meta.findtext(NS.PyWebXML.title) or document.title)
        else:
            links, keywords = [], []
            title = None

        body = newDoc.find(customBody)
        return Document.Document(title, keywords, links, body)
