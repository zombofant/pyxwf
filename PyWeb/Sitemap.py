from __future__ import unicode_literals

import itertools, os

from PyWeb.utils import ET

import PyWeb.Errors as Errors

import PyWeb.utils as utils
import PyWeb.Nodes.Directory as Directory

import PyWeb.Namespaces as NS

import PyWeb.Documents.PyWebXML as PyWebXML

class Site(object):
    namespace = "http://pyweb.zombofant.net/xmlns/site"

    _htmlTag = "{{{0}}}html".format(NS.xhtml)
    _headTag = "{{{0}}}head".format(NS.xhtml)
    _titleTag = "{{{0}}}title".format(NS.xhtml)
    _bodyTag = "{{{0}}}body".format(NS.xhtml)
    _metaTag = "{{{0}}}meta".format(NS.xhtml)

    _localLinkTag = "{{{0}}}a".format(NS.PyWebXML)
    _aTag = "{{{0}}}a".format(NS.xhtml)
    
    def __init__(self, sitemapFileLike=None, **kwargs):
        super(Site, self).__init__(**kwargs)
        self._templateCache = {}
        if sitemapFileLike is not None:
            try:
                self.loadSitemap(ET.parse(sitemapFileLike).getroot())
            except:
                self.clear()
                raise
        else:
            self.clear()

    def _require(self, value, name):
        if value is None:
            raise ValueError("Sitemap requires a valid {0} tag.".format(name))

    def _loadMeta(self, root):
        meta = root.find("{{{0}}}meta".format(self.namespace))
        if meta is None:
            raise ValueError("meta tag must be present.")
        self.title = meta.findtext("{{{0}}}title".format(self.namespace))
        license = meta.find("{{{0}}}license".format(self.namespace))
        if license is not None:
            self.licenseName = unicode(license.text)
            self.licenseHref = unicode(license.get("href", None))

        self.root = meta.findtext("{{{0}}}root".format(self.namespace))
        self.urlRoot = meta.findtext("{{{0}}}urlRoot".format(self.namespace))
        self._require(self.title, "title")
        self._require(self.root, "root")
        self._require(self.urlRoot, "urlRoot")

    def _loadTree(self, tree):
        self.tree = Directory.Directory(None, "tree", tree, self)

    def _getTemplateTransform(self, templateFile):
        cached = self._templateCache.get(templateFile, None)
        if not cached:
            transform = ET.XSLT(ET.parse(os.path.join(self.root, templateFile)))
            self._templateCache[templateFile] = transform
            return transform
        return cached

    def _transformPyNamespace(self, body):
        for localLink in body.iter(self._localLinkTag):
            localLink.tag = self._aTag
            localLink.set("href", os.path.join(self.urlRoot, localLink.get("href")))

    def _applyTemplate(self, title, links, keywords, body, template):
        self._transformPyNamespace(body)
        newDoc = template(body)
        body = newDoc.find(self._bodyTag)
        if body is None:
            raise ValueError("Template did not return a valid body.")
        meta = newDoc.find("{{{0}}}meta".format(NS.PyWebXML))
        if meta is not None:
            addKeywords, addLinks = PyWebXML.PyWebXML.getLinksAndKeywords(meta)
            links = itertools.chain(links, addLinks)
            keywords = list(itertools.chain(keywords, addKeywords))

        html = ET.Element(self._htmlTag)
        head = ET.SubElement(html, self._headTag)
        ET.SubElement(head, self._titleTag).text = title
        for link in links:
            head.append(link)
        if len(keywords) > 0:
            ET.SubElement(head, self._metaTag, attrib={
                "name": "keywords",
                "content": " ".join(keywords)
            })
        html.append(body)
        return ET.ElementTree(html)

    def loadSitemap(self, root):
        self._loadMeta(root)
        tree = root.find("{{{0}}}tree".format(self.namespace))
        self._loadTree(tree)

    def clear(self):
        self.title = None
        self.licenseName = None
        self.licenseHref = None

    def __unicode__(self):
        base = """<Site title={0!r}>""".format(self.title)
        for node in self.tree:
            for line in node.nodeTree():
                base += "\n    "+line
        return base

    def _getNode(self, path, strip=True):
        if strip:
            if not path.startswith(self.urlRoot):
                raise Errors.NotFound(path)
            path = path[len(self.urlRoot):]
        while True:
            try:
                node = self.tree.resolvePath(path, path)
                break
            except Errors.InternalRedirect as redirect:
                path = redirect.to
        return node

    def render(self, path, strip=True):
        node = self._getNode(path, strip)
        doc = node.getDocument()
        links = doc.links
        keywords = doc.keywords
        title = doc.title

        body = doc.body
        template = node.getTemplate()
        transform = self._getTemplateTransform(template)
        return self._applyTemplate(title, links, keywords, body, transform)

