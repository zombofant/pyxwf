# encoding=utf-8
from __future__ import unicode_literals

import itertools, os, importlib, copy, mimetypes

from PyWeb.utils import ET
import PyWeb.Types as Types
import PyWeb.Errors as Errors
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Documents.PyWebXML as PyWebXML
import PyWeb.Message as Message
import PyWeb.Registry as Registry
import PyWeb.Cache as Cache
import PyWeb.Templates as Templates

class Site(object):
    def __init__(self, sitemapFileLike=None, **kwargs):
        super(Site, self).__init__(**kwargs)
        self.cache = Cache.Cache()
        self._templateCache = self.cache[(self, "templates")]
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

    def _loadMimeMap(self, mimeMap):
        for child in mimeMap.findall(NS.Site.mm):
            ext = Types.Typecasts.unicode(child.get("ext"))
            mime = Types.Typecasts.unicode(child.get("type"))
            mimetypes.add_type(mime, ext)

    def _loadTweaks(self, tweaks):
        workingCopy = copy.copy(tweaks)
        perf = workingCopy.find(NS.Site.performance)
        if perf is not None:
            workingCopy.remove(perf)
            self.templateCache = \
                Types.DefaultForNone(True, Types.Typecasts.bool)\
                (perf.get("template-cache"))

        mimeMap = workingCopy.find(getattr(NS.Site, "mime-map"))
        mimetypes.init()
        if mimeMap is not None:
            workingCopy.remove(mimeMap)
            self._loadMimeMap(mimeMap)

        longDate = "%c"
        shortDate = "%c"
        formatting = workingCopy.find(NS.Site.formatting)
        if formatting is not None:
            workingCopy.remove(formatting)
            longDate = formatting.get("date-format") or longDate
            shortDate = formatting.get("date-format") or shortDate
            longDate = formatting.get("long-date-format") or longDate
            shortDate = formatting.get("short-date-format") or shortDate
        self.longDateFormat = longDate
        self.shortDateFormat = shortDate

        for child in workingCopy:
            if child.tag is ET.Comment:
                continue
            ns, name = utils.splitTag(child.tag)
            if ns == NS.Site.xmlns:
                print("Warning: Unknown tweak parameter: {0}".format(name))
        
    def _placeCrumb(self, ctx, crumbNode, crumb):
        tree = crumb.render(ctx)
        crumbParent = crumbNode.getparent()
        crumbNodeIdx = crumbParent.index(crumbNode)
        crumbParent[crumbNodeIdx] = tree

    def getTemplate(self, templateFile):
        if self.templateCache:
            cached = self._templateCache.getDefault(templateFile, None)
        else:
            cached = None
        if not cached:
            templatePath = os.path.join(self.root, templateFile)
            template = Templates.XSLTTemplate(templatePath)
            self._templateCache.add(templatePath, template)
            return template
        return cached

    def transformPyNamespace(self, ctx, body):
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

    def getTemplateArguments(self):
        # XXX: This will possibly explode one day ... 
        return {
            b"site_title": utils.unicodeToXPathStr(self.title)
        }

    def transformHref(self, node, attrName="href"):
        v = node.get(attrName)
        if v is None or "://" in v or v.startswith("/"):  # non local href
            return
        node.set(attrName, os.path.join(self.urlRoot, v))

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
        tweaks = root.find(NS.Site.tweaks)
        if tweaks is not None:
            self._loadTweaks(tweaks)
        self._loadPlugins(root)
        self._loadTree(root)
        self._loadCrumbs(root)

    def clear(self):
        self.title = None
        self.licenseName = None
        self.licenseHref = None

    def handle(self, ctx, strip=True):
        node, remPath = self._getNode(ctx.path, strip)
        ctx.pageNode = node
        template = self.getTemplate(node.Template)
        ctx.template = template
        ctx.overrideLastModified(template.LastModified)
        
        document = node.handle(ctx)
        resultTree = template.final(self, ctx, document)
        
        message = Message.XHTMLMessage(resultTree)
        message.LastModified = document.lastModified
        return message
