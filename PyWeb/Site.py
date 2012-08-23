# encoding=utf-8
"""
The heart of PyWeb is beating in the :cls:`Site` instance. It accepts requests
and passes them through the tree defined in the sitemap xml.
"""
from __future__ import unicode_literals

import itertools, os, importlib, copy, mimetypes, warnings, re, sys

from PyWeb.utils import ET
import PyWeb.Types as Types
import PyWeb.ContentTypes as ContentTypes
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
    """
    Represent and maintain a complete PyWeb framework instance. The sitemap is
    loaded from *sitemapFile*. Optionally, one can specify a *defaultURLRoot*
    which is used if no URL root is specified in the sitemap XML.
    """

    urnScheme = re.compile("^\w+:")

    def __init__(self, sitemapFile, defaultURLRoot=None, **kwargs):
        super(Site, self).__init__(**kwargs)
        self.startCWD = os.getcwd()
        self.defaultURLRoot = defaultURLRoot
        self.cache = Cache.Cache(self)
        # self.savepoint = ImportSavepoints.RollbackImporter()
        try:
            self.loadSitemap(sitemapFile)
        except:
            raise

    @property
    def LastModified(self):
        return self.sitemapTimestamp

    def _require(self, value, name):
        """
        Chech whether the given *value* is None, and if so, raise a ValueError.
        *name* is needed to format a nice error message.
        """
        if value is None:
            raise ValueError("Sitemap requires a valid {0} tag.".format(name))

    def _loadMeta(self, root):
        """
        Process the meta element from a sitemap XML tree.
        """
        meta = root.find(NS.Site.meta)
        if meta is None:
            raise ValueError("meta tag must be present.")

        # pyweb instance name; passed to templates as site_title
        self.title = unicode(meta.findtext(NS.Site.title))

        # file system root when looking for site content files
        self.root = meta.findtext(NS.Site.root) or self.startCWD

        # URL root in the web server setup for absolute links inside the
        # framework (e.g. CSS files)
        self.urlRoot = meta.findtext(NS.Site.urlRoot) or self.defaultURLRoot

        # validate
        self._require(self.title, "title")
        self._require(self.root, "root")
        self._require(self.urlRoot, "urlRoot")

        # set of authors which can be referred by their IDs in documents
        self._authors = {}
        for author in meta.findall(NS.PyWebXML.author):
            authorObj = Document.Author.fromNode(author)
            if authorObj.id is None:
                raise ValueError("Authors must be referrable by an id")
            self._authors[authorObj.id] = authorObj

        # (default) license of content
        license = meta.find(NS.PyWebXML.license)
        if license is not None:
            self._license = Document.License.fromNode(license)
        else:
            self._license = None

    def _loadPlugins(self, root):
        """
        Load the python modules for plugins
        """
        self.nodes = {}
        plugins = root.find(NS.Site.plugins)
        if plugins is None:
            return
        for plugin in plugins.findall(NS.Site.p):
            if not isinstance(plugin.tag, basestring):
                continue
            module = importlib.import_module(plugin.text)

    def _loadTree(self, root):
        """
        Load the whole sitemap tree recursively. Nodes which accept children
        have to load them themselves.
        """
        # find the tree root. This is kinda complicated as we do not
        # know its namespace ...
        for node in root:
            if node.tag.endswith("tree"):
                self.tree = Registry.NodePlugins(node, self, None)
                break
        else:
            raise ValueError("No tree node.")

    def _loadCrumbs(self, root):
        """
        Load crumbs and associate them to their ID.
        """
        self.crumbs = {}
        crumbs = root.find(NS.Site.crumbs)
        if crumbs is None:
            return
        for crumb in crumbs:
            if not isinstance(crumb.tag, basestring):
                continue
            self.addCrumb(Registry.CrumbPlugins(crumb, self))

    def _loadMimeMap(self, mimeMap):
        """
        Load overrides for MIME types.
        """
        for child in mimeMap.findall(NS.Site.mm):
            ext = Types.Typecasts.unicode(child.get("ext"))
            mime = Types.Typecasts.unicode(child.get("type"))
            mimetypes.add_type(mime, ext)

    def _loadTweaks(self, tweaks):
        """
        Load extended configuration (called tweaks).
        """
        workingCopy = copy.copy(tweaks)

        # performance tweaks
        perf = workingCopy.find(NS.Site.performance)
        if perf is not None:
            workingCopy.remove(perf)
        else:
            perf = ET.Element(NS.Site.performance)

        # cache limit
        maxCache = Types.DefaultForNone(0,
            Types.NumericRange(Types.Typecasts.int, 0, None)
        )(perf.get("max-cache-items"))
        # xml pretty printing
        self.cache.Limit = maxCache
        self.prettyPrint = Types.Typecasts.bool(perf.get("pretty-print", False))

        # mime overrides
        mimeMap = workingCopy.find(getattr(NS.Site, "mime-map"))
        mimetypes.init()
        if mimeMap is not None:
            workingCopy.remove(mimeMap)
            self._loadMimeMap(mimeMap)

        # date formatting; defaults to locale specific
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

        # error templates
        self.notFoundTemplate = "templates/errors/not-found.xsl"
        self.defaultTemplate = None
        templates = workingCopy.find(NS.Site.templates)
        if templates is not None:
            workingCopy.remove(templates)
            self.notFoundTemplate = templates.get("not-found",
                    self.notFoundTemplate)
            self.defaultTemplate = templates.get("default",
                    self.defaultTemplate)

        self.htmlTransforms = []
        for transform in list(workingCopy.findall(getattr(NS.Site, "html-transform"))):
            workingCopy.remove(transform)
            self.htmlTransforms.append(Types.NotNone(transform.get("transform")))

        compatibility = workingCopy.find(NS.Site.compatibility)
        if compatibility is None:
            compatibility = ET.Element(NS.Site.compatibility)
        else:
            workingCopy.remove(compatibility)
        self.html4Transform = compatibility.get("html4-transform")

        self._namespaceMap = {}
        self._forceNamespaces = set()
        xmlNamespaces = workingCopy.find(getattr(NS.Site, "xml-namespaces"))
        if xmlNamespaces is None:
            xmlNamespaces = ET.Element(getattr(NS.Site, "xml-namespaces"))
        else:
            workingCopy.remove(xmlNamespaces)
        for ns in xmlNamespaces.findall(NS.Site.ns):
            prefix = ns.get("prefix")
            uri = Types.NotNone(ns.get("uri"))
            force = Types.Typecasts.bool(ns.get("force", False))
            self._namespaceMap[prefix] = uri
            if force:
                self._forceNamespaces.add((prefix, uri))

        # further information, warn about unknown tags in our namespace
        for child in workingCopy:
            if child.tag is ET.Comment:
                continue
            ns, name = utils.splitTag(child.tag)
            if ns == NS.Site.xmlns:
                print("Warning: Unknown tweak parameter: {0}".format(name))
            else:
                try:
                    self.tweakRegistry.submitTweak(child)
                except Errors.MissingTweakPlugin as err:
                    print("Warning: {0}".format(err))

    def _replaceChild(self, parent, oldNode, newNode):
        oldIdx = parent.index(oldNode)
        if newNode is None:
            del parent[oldIdx]
        else:
            parent[oldIdx] = newNode

    def transformReferences(self, ctx, tree):
        """
        Transform references to authors inside the element tree *tree*.
        """
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

    def _placeCrumb(self, ctx, crumbNode, crumb):
        parent = crumbNode.getparent()
        idx = parent.index(crumbNode)
        del parent[idx]
        crumb.render(ctx, parent, idx)

    def transformPyNamespace(self, ctx, body, crumbs=True, a=True, link=True,
            img=True, mobileSwitch=True, contentAttr=True):
        """
        Do PyWeb specific transformations on the XHTML tree *body*. This
        includes transforming local a tags, local img tags and placing crumbs.

        Note that the tree *body* is not bound to be an actual XHTML body.
        This method will iterate over all matching elements, so it can also be
        a whole XHTML html document or just a snippet or something completely
        outside the XHTML namespace.
        """
        if not hasattr(ctx, "crumbCache"):
            ctx.crumbCache = {}
        while crumbs:
            crumbs = False
            for crumbNode in body.iter(NS.PyWebXML.crumb):
                crumbs = True
                crumbID = crumbNode.get("id")
                try:
                    crumb = self.crumbs[crumbID]
                except KeyError:
                    raise ValueError("Invalid crumb id: {0!r}."\
                            .format(crumbID))
                self._placeCrumb(ctx, crumbNode, crumb)

        if a:
            for localLink in body.iter(NS.PyWebXML.a):
                localLink.tag = NS.XHTML.a
                self.transformHref(ctx, localLink)
        if img:
            for localImg in body.iter(NS.PyWebXML.img):
                localImg.tag = NS.XHTML.img
                self.transformHref(ctx, localImg)
                localImg.set("src", localImg.get("href"))
                del localImg.attrib["href"]
        if link:
            for localLink in body.iter(NS.PyWebXML.link):
                localLink.tag = NS.XHTML.link
                if localLink.get("href"):
                    self.transformHref(ctx, localLink)
        if mobileSwitch:
            toDelete = set()
            for mobileSwitch in body.iter(getattr(NS.PyWebXML, "if-mobile")):
                if Types.Typecasts.bool(mobileSwitch.get("mobile", True)) != ctx.IsMobileClient:
                    toDelete.add(mobileSwitch)
                    continue

                mobileSwitch.tag = getattr(NS.XHTML, mobileSwitch.get("xhtml-element", "span"))
            for mobileSwitch in toDelete:
                mobileSwitch.getparent().remove(mobileSwitch)
        if contentAttr:
            contentAttrName = NS.PyWebXML.content
            contentMakeURIAttrName = getattr(NS.PyWebXML, "content-make-uri")
            for el in body.iterfind(".//*[@{0}]".format(contentAttrName)):
                makeURI = el.get(contentMakeURIAttrName)
                if makeURI is not None:
                    del el.attrib[contentMakeURIAttrName]
                    makeGlobal = Types.Typecasts.bool(makeURI)
                else:
                    makeGlobal = False
                el.set("content", el.get(contentAttrName))
                del el.attrib[contentAttrName]
                self.transformHref(ctx, el, "content", makeGlobal=makeGlobal)


    def getTemplateArguments(self, ctx):
        # XXX: This will possibly explode one day ...
        return {
            b"site_title": utils.unicodeToXPathStr(self.title),
            b"mobile_client": "1" if ctx.IsMobileClient else "0"
        }

    def transformHref(self, ctx, node, attrName="href", makeGlobal=False):
        """
        Transform the attribute *attrName* on the ETree node *node* as if it
        was a possibly local url. If it is local and relative, it gets
        transformed so that it points to the same location independent of the
        current URL.
        """
        v = node.get(attrName)
        if v is None or v.startswith("/") or self.urnScheme.search(v):  # non local href
            return
        value = os.path.join(self.urlRoot, v)
        if makeGlobal:
            value = "{0}://{1}{2}".format(ctx.URLScheme, ctx.HostName, value)
        node.set(attrName, value)


    def _getNode(self, ctx):
        """
        Find the node pointed to by the *Path* stored in the Context *ctx*.
        """
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
        """
        Add the given *crumb* to the Sites crumb registry. May throw a
        ValueError if the ID is invalied or duplicated with an already existing
        registry entry.
        """
        if crumb.ID is None:
            raise ValueError("Crumb declared without id.")
        if crumb.ID in self.crumbs:
            raise ValueError("Duplicate crumb id: {0}".format(crumb.ID))
        self.crumbs[crumb.ID] = crumb

    def registerNodeID(self, ID, node):
        """
        Nodes may have IDs under which they can be referred using the Site. This
        method is used to register the *node* under a given *ID*. This will
        raise a ValueError if the ID is duplicated.
        """
        #if ID in self.nodes:
        #    raise ValueError("Duplicate node id: {0}".format(ID))
        self.nodes[ID] = node

    def getNode(self, ID):
        """
        Retrieve the node which has the ID *ID*.
        """
        return self.nodes[ID]

    def _setupCache(self, key, cls, *args):
        """
        Setup a cache with *key* and class *cls* passing *args* to its
        constructor as a specialized Cache in our *cache* attribute.
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
        return self.cache.specializedCache(key, cls, *args)

    def loadSitemap(self, sitemapFile):
        """
        Load the whole sitemap XML from *sitemapFile*.
        """
        # set this up for later auto-reload
        self.sitemapFile = sitemapFile
        self.sitemapTimestamp = utils.fileLastModified(sitemapFile)

        # parse the sitemap
        root = ET.parse(sitemapFile).getroot()

        # load metadata
        self._loadMeta(root)

        # setup specialized caches
        self.templateCache = self._setupCache((self, "templates"),
            Templates.XSLTTemplateCache, self.root)
        self.fileDocumentCache = self._setupCache((self, "file-doc-cache"),
            Document.FileDocumentCache, self.root)
        self.xmlDataCache = self._setupCache((self, "xml-data-cache"),
            Resource.XMLFileCache, self.root)
        self.parserRegistry = Registry.ParserRegistry()
        self.tweakRegistry = Registry.TweakRegistry()
        self.hooks = Registry.HookRegistry()

        # load plugins
        self._loadPlugins(root)

        # instanciate sitletons, so they're ready when the tweaks come in
        self.sitletons = Registry.Sitletons.instanciate(self)

        # load extended configuration
        tweaks = root.find(NS.Site.tweaks)
        if tweaks is None:
            tweaks = ET.Element(NS.Site.tweaks)
        self._loadTweaks(tweaks)

        # load site tree
        self._loadTree(root)

        # setup the default template
        if self.defaultTemplate is None:
            self.defaultTemplate = self.tree.Template or "templates/default.xsl"

        # load crumbs
        self._loadCrumbs(root)

    def update(self):
        """
        If neccessary, reload the whole sitemap. Print a warning to the log, as
        this is still fragile.
        """
        sitemapTimestamp = utils.fileLastModified(self.sitemapFile)
        if sitemapTimestamp > self.sitemapTimestamp:
            print("sitemap xml changed -- reloading COMPLETE site.")
            # Registry.clearAll()
            # self.savepoint.rollback()
            self.loadSitemap(self.sitemapFile)

    def handleNotFound(self, ctx, resourceName):
        """
        Handle a NotFound exception if it occurs while traversing the sitetree
        in the search for a node to handle the current request.
        """
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

    def getMessage(self, ctx):
        """
        Handle a request in the given Context *ctx*.
        """
        # mark ourselves as a used resource
        ctx.useResource(self)

        # call a hook used by some tweaks
        self.hooks.call("handle.pre-lookup", ctx)

        # prepare iterable with loaded html transformations
        htmlTransforms = itertools.imap(self.templateCache.__getitem__, \
            self.htmlTransforms)

        # default status code
        status = 200
        try:
            # attempt lookup
            node = self._getNode(ctx)
        except Errors.HTTP.NotFound as err:
            if err.document is not None:
                data = err.document
                template = err.template
            else:
                data = self.handleNotFound(ctx,
                        err.resourceName or ctx.Path)
                template = None
            if template is None:
                template = self.templateCache[self.defaultTemplate]
            status = err.statusCode
        else:
            # setup the context
            ctx._pageNode = node
            # load the template and mark it for use
            template = self.templateCache[node.Template]
            ctx.useResource(template)

            # evaluate the iterable as we need the list multiple times in this
            # code path
            htmlTransforms = list(htmlTransforms)
            ctx.useResources(htmlTransforms)

            contentType = node.getContentType(ctx)
            ctx.checkAcceptable(contentType)

            if contentType == ContentTypes.xhtml:
                if not ctx.HTML5Support and self.html4Transform:
                    ctx.useResource(self.templateCache[self.html4Transform])

            # raise NotModified if the result will be available on the client
            # side
            ctx.checkNotModified()

            # otherwise, create the document and return it
            data = node.handle(ctx)

        if isinstance(data, Document.Document):
            # do the final transformation on the content fetched from the node
            resultTree = template.final(ctx, data,
                    licenseFallback=self._license)

            for xslt in htmlTransforms:
                resultTree = xslt.rawTransform(resultTree, {})

            if not ctx.HTML5Support and self.html4Transform:
                transform = self.templateCache[self.html4Transform]
                resultTree = transform.rawTransform(resultTree, {})

            if not ctx.CanUseXHTML:
                message = Message.HTMLMessage.fromXHTMLTree(resultTree,
                    statusCode=status, encoding="utf-8",
                    prettyPrint=self.prettyPrint
                )
            else:
                message = Message.XHTMLMessage(resultTree,
                    statusCode=status, encoding="utf-8",
                    prettyPrint=self.prettyPrint,
                    forceNamespaces=dict(self._forceNamespaces)
                )
        elif isinstance(data, (ET._Element, ET._ElementTree)):
            message = Message.XMLMessage(data, contentType,
                statusCode=status, encoding="utf-8",
                cleanupNamespaces=True, prettyPrint=self.prettyPrint
            )
        elif isinstance(data, basestring):
            message = Message.TextMessage(data, contentType,
                statusCode=status, encoding="utf-8"
            )
        else:
            raise TypeError("Cannot process node result: {0}".format(type(data)))
        # only enforce at the end of a request, otherwise things may become
        # horribly slow if more resources are needed than the cache allows
        self.cache.enforceLimit()
        return message

    def handle(self, ctx):
        try:
            return self.getMessage(ctx)
        except Errors.Handler.InternalServerError as err:
            return Message.HTMLMessage.fromXHTMLTree(err.xhtml, statusCode=500,
                encoding="utf-8")
        except Errors.HTTPException:
            raise
        except Exception as err:
            xhtml = Errors.Handler.InternalServerError(ctx, *sys.exc_info()).xhtml
            return Message.HTMLMessage.fromXHTMLTree(xhtml, statusCode=500,
                encoding="utf-8")
