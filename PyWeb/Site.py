# encoding=utf-8
from __future__ import unicode_literals

import itertools, os, importlib, copy

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
        self.title = unicode(meta.findtext(NS.Site.title))
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
        self.nodes = {}
        plugins = root.find(NS.Site.plugins)
        if plugins is None:
            return
        for plugin in plugins.findall(NS.Site.p):
            if not isinstance(plugin.tag, basestring):
                continue
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
    
    def _loadCrumbs(self, root):
        self.crumbs = {}
        crumbs = root.find(NS.Site.crumbs)
        for crumb in crumbs:
            if not isinstance(crumb.tag, basestring):
                continue 
            self.addCrumb(Registry.CrumbPlugins(crumb, self))

    def _loadTweaks(self, tweaks):
        workingCopy = copy.copy(tweaks)
        perf = workingCopy.find(NS.Site.performance)
        if perf is not None:
            workingCopy.remove(perf)
            self.templateCache = utils.getBoolAttr(perf, "template-cache", True)

        for child in workingCopy:
            if child.tag is ET.Comment:
                continue
            print(child.tag)
            ns, name = utils.splitTag(child)
            if ns == NS.Site.xmlns:
                print("Warning: Unknown tweak parameter: {0}".format(name))

    def _getTemplateTransform(self, templateFile):
        if self.templateCache:
            cached = self._templateCache.get(templateFile, None)
        else:
            cached = None
        if not cached:
            transform = ET.XSLT(ET.parse(os.path.join(self.root, templateFile)))
            self._templateCache[templateFile] = transform
            return transform
        return cached
        
    def _placeCrumb(self, ctx, crumbNode, crumb):
        tree = crumb.render(ctx)
        crumbParent = crumbNode.getparent()
        crumbNodeIdx = crumbParent.index(crumbNode)
        crumbParent[crumbNodeIdx] = tree

    def _transformPyNamespace(self, ctx, body):
        crumbs = True
        while crumbs:
            crumbs = False
            for crumbNode in body.iter(NS.PyWebXML.crumb):
                crumbs = True
                crumbID = crumbNode.get("id")
                try:
                    crumb = self.crumbs[crumbID]
                except KeyError:
                    raise ValueError("Invalid crumb id: {0!r}.".format(crumbID))
                self._placeCrumb(ctx, crumbNode, crumb)
        for localLink in body.iter(NS.PyWebXML.a):
            localLink.tag = NS.XHTML.a
            localPath = localLink.get("href")
            if len(localPath) > 0 and localPath[0] == "/":
                localPath = localPath[1:]
            localLink.set("href", os.path.join(self.urlRoot, localPath))
            

    def _getTemplateArguments(self, document):
        return {
            b"doc_title": repr(document.title)[1:],
            b"site_title": repr(self.title)[1:]
        }

    def _transformHref(self, node, attrName="href"):
        v = node.get(attrName)
        print("WARNING: MISSING NONLOCAL DETECTION")
        if v[:1] == "/":
            v = v[1:]
        node.set(attrName, os.path.join(self.urlRoot, v))

    def _applyTemplate(self, ctx, document, transform):
        links = document.links
        keywords = document.keywords
        templateArgs = self._getTemplateArguments(document)
        newDoc = transform(document.body, **templateArgs)
        body = newDoc.find(NS.XHTML.body)
        ctx.body = body
        self._transformPyNamespace(ctx, body)
        if body is None:
            raise ValueError("Template did not return a valid body.")
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
            self._transformHref(link)
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
    
    def addCrumb(self, crumb):
        if crumb.ID is None:
            raise ValueError("Crumb declared without id.")
        if crumb.ID in self.crumbs:
            raise ValueError("Duplicate crumb id: {0}".format(crumb.ID))
        self.crumbs[crumb.ID] = crumb
        
    def registerNodeID(self, ID, node):
        if ID in self.nodes:
            raise ValueError("Duplicate node id: {0}".format(ID))
        self.nodes[ID] = node
        
    def getNode(self, ID):
        return self.nodes[ID]

    def loadSitemap(self, root):
        self._loadMeta(root)
        self._loadPlugins(root)
        self._loadTree(root)
        self._loadCrumbs(root)
        tweaks = root.find(NS.Site.tweaks)
        if tweaks is not None:
            self._loadTweaks(tweaks)

    def clear(self):
        self.title = None
        self.licenseName = None
        self.licenseHref = None

    def handle(self, ctx, strip=True):
        node, remPath = self._getNode(ctx.path, strip)
        ctx.pageNode = node
        document = node.handle(ctx, remPath)
        transform = self._getTemplateTransform(node.Template)
        resultTree = self._applyTemplate(ctx, document, transform)
        return Message.XHTMLMessage(resultTree)
