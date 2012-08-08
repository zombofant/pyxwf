# encoding=utf-8
from __future__ import unicode_literals

import itertools, os, importlib, copy, mimetypes, warnings

from PyWeb.utils import ET
import PyWeb.Types as Types
import PyWeb.Errors as Errors
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.Parsers.PyWebXML as PyWebXML
import PyWeb.Message as Message
import PyWeb.Document as Document
import PyWeb.Registry as Registry
import PyWeb.Cache as Cache
import PyWeb.Templates as Templates
import PyWeb.Resource as Resource
# import PyWeb.ImportSavepoints as ImportSavepoints

class Site(Resource.Resource):
    def __init__(self, sitemapFile, defaultURLRoot=None, **kwargs):
        super(Site, self).__init__(**kwargs)
        self.startCWD = os.getcwd()
        self.defaultURLRoot = defaultURLRoot
        self.cache = Cache.Cache()
        self.hooks = Registry.HookRegistry()
        # self.savepoint = ImportSavepoints.RollbackImporter()
        try:
            self.loadSitemap(sitemapFile)
        except:
            raise
        self.sitletons = Registry.Sitletons.instanciate(self)

    @property
    def LastModified(self):
        return self.sitemapTimestamp

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

        self.root = meta.findtext(NS.Site.root) or self.startCWD
        self.urlRoot = meta.findtext(NS.Site.urlRoot) or self.defaultURLRoot
        print("configured url root: {0}".format(self.urlRoot))
        self._require(self.title, "title")
        self._require(self.root, "root")
        self._require(self.urlRoot, "urlRoot")

        self._authors = {}
        for author in meta.findall(NS.PyWebXML.author):
            authorObj = Document.Author.fromNode(author)
            if authorObj.id is None:
                raise ValueError("Authors must be referrable by an id")
            self._authors[authorObj.id] = authorObj

        license = meta.find(NS.PyWebXML.license)
        if license is not None:
            self._license = Document.License.fromNode(license)
        else:
            self._license = None

    def _loadPlugins(self, root):
        self.nodes = {}
        plugins = root.find(NS.Site.plugins)
        if plugins is None:
            return
        for plugin in plugins.findall(NS.Site.p):
            if not isinstance(plugin.tag, basestring):
                continue
            module = importlib.import_module(plugin.text)

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
            maxCache = Types.DefaultForNone(0,
                Types.NumericRange(Types.Typecasts.int, 0, None)
            )(perf.get("max-cache-items"))
            self.cache.Limit = maxCache

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

        self.notFoundTemplate = "templates/errors/not-found.xsl"
        self.defaultTemplate = None

        templates = workingCopy.find(NS.Site.templates)
        if templates is not None:
            workingCopy.remove(templates)
            self.notFoundTemplate = templates.get("not-found",
                    self.notFoundTemplate)
            self.defaultTemplate = templates.get("default",
                    self.defaultTemplate)

        for child in workingCopy:
            if child.tag is ET.Comment:
                continue
            ns, name = utils.splitTag(child.tag)
            if ns == NS.Site.xmlns:
                print("Warning: Unknown tweak parameter: {0}".format(name))
            else:
                try:
                    Registry.TweakPlugins(child)
                except Errors.MissingTweakPlugin as err:
                    print("Warning: {0}".format(err))

    def _placeCrumb(self, ctx, crumbNode, crumb):
        tree = crumb.render(ctx)
        crumbParent = crumbNode.getparent()
        crumbNodeIdx = crumbParent.index(crumbNode)
        if tree is not None:
            crumbParent[crumbNodeIdx] = tree
        else:
            del crumbParent[crumbNodeIdx]

    def transformReferences(self, ctx, tree):
        for author in tree.iter(NS.PyWebXML.author):
            id = author.get("id")
            if id:
                try:
                    authorObj = self._authors[id]
                except KeyError:
                    author.tag = NS.XHTML.span
                    author.text = "AUTHOR NOT FOUND {0}".format(id)
                    continue
                authorObj.applyToNode(author)

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
            self.transformHref(localLink)
        for localImg in body.iter(NS.PyWebXML.img):
            localImg.tag = NS.XHTML.img
            self.transformHref(localImg)
            localImg.set("src", localImg.get("href"))
            del localImg.attrib["href"]

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

    def _getNode(self, ctx):
        path = ctx.Path
        if len(path) > 0 and path[0] == "/":
            path = path[1:]
        try:
            node = self.tree.resolvePath(ctx, path)
        except Errors.InternalRedirect as redirect:
            ctx.Path = redirect.newLocation
            return self._getNode(ctx)
        return node

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

    def _setupCache(self, key, cls, *args):
        try:
            del self.cache[key]
        except KeyError:
            pass
        return self.cache.specializedCache(key, cls, *args)

    def loadSitemap(self, sitemapFile):
        self.sitemapFile = sitemapFile
        self.sitemapTimestamp = utils.fileLastModified(sitemapFile)

        root = ET.parse(sitemapFile).getroot()
        self._loadMeta(root)

        self.templateCache = self._setupCache((self, "templates"),
            Templates.XSLTTemplateCache, self.root)
        self.fileDocumentCache = self._setupCache((self, "file-doc-cache"),
            Document.FileDocumentCache, self.root)

        self._loadPlugins(root)
        tweaks = root.find(NS.Site.tweaks)
        if tweaks is not None:
            self._loadTweaks(tweaks)
        self._loadTree(root)
        if self.defaultTemplate is None:
            self.defaultTemplate = self.tree.Template or "templates/default.xsl"
        self._loadCrumbs(root)

    def clear(self):
        self.title = None
        self.licenseName = None
        self.licenseHref = None

    def update(self):
        sitemapTimestamp = utils.fileLastModified(self.sitemapFile)
        if sitemapTimestamp > self.sitemapTimestamp:
            print("sitemap xml changed -- reloading COMPLETE site.")
            # Registry.clearAll()
            # self.savepoint.rollback()
            self.loadSitemap(self.sitemapFile)

    def handleNotFound(self, ctx, resourceName):
        try:
            tpl = self.templateCache[self.notFoundTemplate]
        except Exception as err:
            warnings.warn(str(err))
            body = ET.Element(NS.XHTML.body)
            section = ET.SubElement(body, NS.XHTML.section)
            header = ET.SubElement(section, NS.XHTML.header)
            h2 = ET.SubElement(header, NS.XHTML.h2)
            h2.text = "Resource not found"
            p = ET.SubElement(section, NS.XHTML.p)
            p.text = "The resource {0} could not be found.".format(resourceName)
            p = ET.SubElement(section, NS.XHTML.p)
            p.text = "Additionally, the specified (or fallback) error template\
 at {0} could not be loaded: {1}.".format(self.notFoundTemplate,
                type(err).__name__)
            return Document.Document("Not found", [], [], body)
        else:
            err = ET.Element(NS.PyWebXML.error, attrib={
                "type": "not-found"
            })
            ET.SubElement(err, NS.PyWebXML.resource).text = resourceName
            return tpl.transform(err, {})


    def handle(self, ctx):
        ctx.useResource(self)
        self.hooks.call("handle.pre-lookup", ctx)
        status = 200
        try:
            node = self._getNode(ctx)
        except Errors.HTTP.NotFound as err:
            if err.document is not None:
                document = err.document
                template = err.template
            else:
                document = self.handleNotFound(ctx,
                        err.resourceName or ctx.Path)
                template = None
            if template is None:
                template = self.templateCache[self.defaultTemplate]
            status = err.statusCode
        else:
            ctx._pageNode = node
            template = self.templateCache[node.Template]
            ctx.useResource(template)

            ctx.checkNotModified()
            document = node.handle(ctx)

        resultTree = template.final(self, ctx, document,
                licenseFallback=self._license)

        message = Message.XHTMLMessage(resultTree, statusCode=status)
        # only enforce at the end of a request, otherwise things may become
        # horribly slow if more resources are needed than the cache allows
        self.cache.enforceLimit()
        return message
