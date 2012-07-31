import abc, itertools

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Cache as Cache
import PyWeb.Namespaces as NS
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
    def apply(self, site, ctx, xhtmlBody):
        pass


class XSLTTemplate(Template):
    def __init__(self, fileName):
        super(XSLTTemplate, self).__init__(fileName)
        self._parseTemplate()

    def _reload(self):
        self._parseTemplate()

    def _parseTemplate(self):
        self.transform = ET.XSLT(ET.parse(self.fileName))

    def apply(self, site, ctx, document):
        links, keywords = document.links, document.keywords
        
        templateArgs = site.getTemplateArguments()
        templateArgs.update(document.getTemplateArguments())
        
        newDoc = self.transform(document.body, **templateArgs)
        
        body = newDoc.find(NS.XHTML.body)
        ctx.body = body
        
        site.transformPyNamespace(ctx, body)
        
        if body is None:
            raise ValueError("Transform did not return a valid body.")
        
        meta = newDoc.find(NS.PyWebXML.meta)
        if meta is not None:
            addKeywords, addLinks = PyWebXML.PyWebXML.getLinksAndKeywords(meta)
            links = itertools.chain(links, addLinks)
            keywords = list(itertools.chain(keywords, addKeywords))
            title = unicode(meta.findtext(NS.PyWebXML.title) or document.title)
        else:
            title = document.title

        html = ET.Element(NS.XHTML.html)
        head = ET.SubElement(html, NS.XHTML.head)
        ET.SubElement(head, NS.XHTML.title).text = title
        for link in links:
            site.transformHref(link)
            head.append(link)
        if len(keywords) > 0:
            ET.SubElement(head, NS.XHTML.meta, attrib={
                "name": "keywords",
                "content": " ".join(keywords)
            })
        html.append(body)
        
        return ET.ElementTree(html)
