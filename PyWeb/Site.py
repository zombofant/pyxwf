# encoding=utf-8
from __future__ import unicode_literals

import itertools, os, importlib

from PyWeb.utils import ET

import PyWeb.Errors as Errors
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Documents.PyWebXML as PyWebXML
import PyWeb.Message as Message
import PyWeb.Registry as Registry

class Site(object):
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
        meta = root.find(NS.Site.meta)
        if meta is None:
            raise ValueError("meta tag must be present.")
        self.title = meta.findtext(NS.Site.title)
        license = meta.find(NS.Site.license)
        if license is not None:
            self.licenseName = unicode(license.text)
            self.licenseHref = unicode(license.get("href", None))

        self.root = meta.findtext(NS.Site.root)
        self.urlRoot = meta.findtext(NS.Site.urlRoot)
        self._require(self.title, "title")
        self._require(self.root, "root")
        self._require(self.urlRoot, "urlRoot")

    def _loadPlugins(self, root):
        plugins = root.find(NS.Site.plugins)
        if plugins is None:
            return
        for plugin in plugins.findall(NS.Site.p):
            importlib.import_module(plugin.text)

    def _loadTree(self, root):
        # find the tree root. This is kinda complicated as we do not
        # know its namespace ...
        for node in root:
            if node.tag.endswith("tree"):
                self.tree = Registry.NodePlugins(node, self, None)
                break
        else:
            raise ValueError("No tree node.")

    def _getTemplateTransform(self, templateFile):
        cached = self._templateCache.get(templateFile, None)
        if not cached:
            transform = ET.XSLT(ET.parse(os.path.join(self.root, templateFile)))
            self._templateCache[templateFile] = transform
            return transform
        return cached

    def _transformPyNamespace(self, body):
        for localLink in body.iter(NS.PyWebXML.a):
            localLink.tag = NS.XHTML.a
            localLink.set("href", os.path.join(self.urlRoot, localLink.get("href")))

    def _applyTemplate(self, title, links, keywords, body, template):
        self._transformPyNamespace(body)
        newDoc = template(body)
        body = newDoc.find(NS.XHTML.body)
        if body is None:
            raise ValueError("Template did not return a valid body.")
        meta = newDoc.find(NS.PyWebXML.meta)
        if meta is not None:
            addKeywords, addLinks = PyWebXML.PyWebXML.getLinksAndKeywords(meta)
            links = itertools.chain(links, addLinks)
            keywords = list(itertools.chain(keywords, addKeywords))

        html = ET.Element(NS.XHTML.html)
        head = ET.SubElement(html, NS.XHTML.head)
        ET.SubElement(head, NS.XHTML.title).text = title
        for link in links:
            head.append(link)
        if len(keywords) > 0:
            ET.SubElement(head, NS.XHTML.meta, attrib={
                "name": "keywords",
                "content": " ".join(keywords)
            })
        html.append(body)
        return ET.ElementTree(html)

    def _getNode(self, path, strip=True):
        if strip:
            if not path.startswith(self.urlRoot):
                raise Errors.NotFound(path)
            path = path[len(self.urlRoot):]
        if len(path) > 0 and path[0] == "/":
            path = path[1:]
        while True:
            try:
                node, remPath = self.tree.resolvePath(path, path)
                break
            except Errors.InternalRedirect as redirect:
                path = redirect.to
        return node, remPath

    def loadSitemap(self, root):
        self._loadMeta(root)
        self._loadPlugins(root)
        self._loadTree(root)

    def clear(self):
        self.title = None
        self.licenseName = None
        self.licenseHref = None

    def render(self, document, template):
        transform = self._getTemplateTransform(template)
        return self._applyTemplate(
            document.title,
            document.links,
            document.keywords,
            document.body,
            transform)

    def handle(self, request, strip=True):
        node, remPath = self._getNode(request.path, strip)
        document = node.handle(request, remPath)
        resultTree = self.render(document, node.getTemplate())
        return Message.XHTMLMessage(resultTree)
