# encoding=utf-8
"""
The heart of PyXWF is beating in the :class:`~Site` instance. It accepts requests
and passes them through the tree defined in the sitemap xml.
"""
from __future__ import unicode_literals

import itertools, os, importlib, copy, mimetypes, warnings, re, sys, logging

from PyXWF.utils import ET, _F, threading, blist
import PyXWF
import PyXWF.Types as Types
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Errors as Errors
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Parsers.PyWebXML as PyWebXML
import PyXWF.Message as Message
import PyXWF.Document as Document
import PyXWF.Registry as Registry
import PyXWF.Cache as Cache
import PyXWF.Templates as Templates
import PyXWF.Resource as Resource
# import PyXWF.ImportSavepoints as ImportSavepoints

class Site(Resource.Resource):
    """
    Represent and maintain a complete PyXWF framework instance. The sitemap is
    loaded from *sitemap_file*. Optionally, one can specify a *default_url_root*
    which is used if no URL root is specified in the sitemap XML.

    .. attribute:: parser_registry

        An instance of :class:`~PyXWF.Registry.ParserRegistry` local to the
        current site. This is the preferred method to access parsers.

    .. attribute:: hooks

        An instance of :class:`~PyXWF.Registry.HookRegistry` for this site.
        See :ref:`site-hooks` for a reference of existing hooks.
    """

    urn_scheme = re.compile("^\w+:")

    def __init__(self, sitemap_file, default_url_root=None, **kwargs):
        logging.info(_F(
"Initializing PyXWF/{pyxwf_version} at {pid} with lxml.etree/{etree_version}, {threading}, blist/{blist_version}",
            pyxwf_version=PyXWF.__version__,
            etree_version=ET.__version__,
            threading=threading.__name__,
            blist_version=blist.__version__,
            pid=os.getpid()
        ))
        super(Site, self).__init__(**kwargs)
        self.startcwd = os.getcwd()
        self.default_url_root = default_url_root
        self.cache = Cache.Cache(self)
        # self.savepoint = ImportSavepoints.RollbackImporter()
        try:
            self.load_sitemap(sitemap_file)
        except:
            raise

    @property
    def LastModified(self):
        return self.sitemap_timestamp

    def _require(self, value, name):
        """
        Chech whether the given *value* is None, and if so, raise a ValueError.
        *name* is needed to format a nice error message.
        """
        if value is None:
            raise ValueError("Sitemap requires a valid {0} tag.".format(name))

    def _load_meta(self, root):
        """
        Process the meta element from a sitemap XML tree.
        """
        meta = root.find(NS.Site.meta)
        if meta is None:
            raise ValueError("meta tag must be present.")

        # pyxwf instance name; passed to templates as site_title
        self.title = unicode(meta.findtext(NS.Site.title))

        # file system root when looking for site content files
        self.root = meta.findtext(NS.Site.root) or self.startcwd

        # URL root in the web server setup for absolute links inside the
        # framework (e.g. CSS files)
        self.urlroot = meta.findtext(NS.Site.urlroot) or self.default_url_root

        # validate
        self._require(self.title, "title")
        self._require(self.root, "root")
        self._require(self.urlroot, "urlroot")

        # set of authors which can be referred by their IDs in documents
        self._authors = {}
        for author in meta.findall(NS.PyWebXML.author):
            authorobj = Document.Author.from_node(author)
            if authorobj.id is None:
                raise ValueError("Authors must be referrable by an id")
            self._authors[authorobj.id] = authorobj

        # (default) license of content
        license = meta.find(NS.PyWebXML.license)
        if license is not None:
            self._license = Document.License.from_node(license)
        else:
            self._license = None

    def _load_plugins(self, root):
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

    def _load_tree(self, root):
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

    def _load_crumbs(self, root):
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
            self.add_crumb(Registry.CrumbPlugins(crumb, self))

    def _load_mimemap(self, mimemap):
        """
        Load overrides for MIME types.
        """
        for child in mimemap.findall(NS.Site.mm):
            ext = Types.Typecasts.unicode(child.get("ext"))
            mime = Types.Typecasts.unicode(child.get("type"))
            mimetypes.add_type(mime, ext)

    def _load_tweaks(self, tweaks):
        """
        Load extended configuration (called tweaks).
        """
        working_copy = copy.copy(tweaks)

        # performance tweaks
        perf = working_copy.find(NS.Site.performance)
        if perf is not None:
            working_copy.remove(perf)
        else:
            perf = ET.Element(NS.Site.performance)

        # cache limit
        try:
            maxcache = Types.NumericRange(Types.Typecasts.int, 0, None)\
                    (perf.attrib.pop("cache-limit"))
        except KeyError:
            maxcache = 0
        # xml pretty printing
        self.cache.Limit = maxcache
        try:
            self.pretty_print = Types.Typecasts.bool(perf.attrib.pop("pretty-print"))
        except KeyError:
            self.pretty_print = False
        if len(perf.attrib):
            logging.debug(_F("Unused attributes on <performance />: {0}", perf.attrib))

        # mime overrides
        mimemap = working_copy.find(getattr(NS.Site, "mime-map"))
        mimetypes.init()
        if mimemap is not None:
            working_copy.remove(mimemap)
            self._load_mimemap(mimemap)

        # date formatting; defaults to locale specific
        long_date = "%c"
        short_date = "%c"
        formatting = working_copy.find(NS.Site.formatting)
        if formatting is not None:
            working_copy.remove(formatting)
            long_date = formatting.get("date-format") or long_date
            short_date = formatting.get("date-format") or short_date
            long_date = formatting.get("long-date-format") or long_date
            short_date = formatting.get("short-date-format") or short_date
        self.long_date_format = long_date
        self.short_date_format = short_date

        # error templates
        self.not_found_template = "templates/errors/not-found.xsl"
        self.default_template = None
        templates = working_copy.find(NS.Site.templates)
        if templates is not None:
            working_copy.remove(templates)
            self.not_found_template = templates.get("not-found",
                    self.not_found_template)
            self.default_template = templates.get("default",
                    self.default_template)

        self.html_transforms = []
        for transform in list(working_copy.findall(getattr(NS.Site, "html-transform"))):
            working_copy.remove(transform)
            self.html_transforms.append(Types.NotNone(transform.get("transform")))

        compatibility = working_copy.find(NS.Site.compatibility)
        if compatibility is None:
            compatibility = ET.Element(NS.Site.compatibility)
        else:
            working_copy.remove(compatibility)
        self.html4_transform = compatibility.get("html4-transform")

        self._namespacemap = {}
        self._force_namespaces = set()
        xml_namespaces = working_copy.find(getattr(NS.Site, "xml-namespaces"))
        if xml_namespaces is None:
            xml_namespaces = ET.Element(getattr(NS.Site, "xml-namespaces"))
        else:
            working_copy.remove(xml_namespaces)
        for ns in xml_namespaces.findall(NS.Site.ns):
            prefix = ns.get("prefix")
            uri = Types.NotNone(ns.get("uri"))
            force = Types.Typecasts.bool(ns.get("force", False))
            self._namespacemap[prefix] = uri
            if force:
                self._force_namespaces.add((prefix, uri))

        # further information, warn about unknown tags in our namespace
        for child in working_copy:
            if child.tag is ET.Comment:
                continue
            ns, name = utils.split_tag(child.tag)
            if ns == NS.Site.xmlns:
                logging.warning("Unknown tweak parameter: {0}".format(name))
            else:
                try:
                    self.tweak_registry.submit_tweak(child)
                except Errors.MissingTweakPlugin as err:
                    logging.warning(unicode(err))

    def _replace_child(self, parent, old_node, new_node):
        old_idx = parent.index(old_node)
        if new_node is None:
            del parent[old_idx]
        else:
            parent[old_idx] = new_node

    def transform_references(self, ctx, tree):
        """
        Transform all ``<py:author />`` elements in *tree* which have an ``@id``
        attribute by copying all relevant attributes of the
        :class:`~PyXWF.Document.Author` object referred to by the ``@id`` to the
        element. This overrides existing attributes.

        If the ``@id`` is not known to the site, the text of the element is
        replaced with a easy-to-recognize placeholder and the element is
        converted to a ``<h:span />`` element.
        """
        for author in tree.iter(NS.PyWebXML.author):
            id = author.get("id")
            if id:
                try:
                    authorobj = self._authors[id]
                except KeyError:
                    author.tag = NS.XHTML.span
                    author.text = "AUTHOR NOT FOUND {0}".format(id)
                    continue
                authorobj.apply_to_node(author)

    def _place_crumb(self, ctx, crumb_node, crumb):
        parent = crumb_node.getparent()
        idx = parent.index(crumb_node)
        del parent[idx]
        crumb.render(ctx, parent, idx)

    def transform_py_namespace(self, ctx, body, crumbs=True, a=True, link=True,
            img=True, mobile_switch=True, content_attr=True):
        """
        Do PyXWF specific transformations on the XHTML tree *body*. This
        includes transforming local a tags, local img tags and placing crumbs.

        Note that the tree *body* is not bound to be an actual XHTML body.
        This method will iterate over all matching elements, so it can also be
        a whole XHTML html document or just a snippet or something completely
        outside the XHTML namespace.

        See :ref:`<py-namespace>` for documentation on what can be done with
        in that XML namespace.
        """
        if not hasattr(ctx, "crumb_cache"):
            ctx.crumb_cache = {}
        while crumbs:
            crumbs = False
            for crumb_node in body.iter(NS.PyWebXML.crumb):
                crumbs = True
                crumb_id = crumb_node.get("id")
                try:
                    crumb = self.crumbs[crumb_id]
                except KeyError:
                    raise ValueError("Invalid crumb id: {0!r}."\
                            .format(crumb_id))
                self._place_crumb(ctx, crumb_node, crumb)

        if a:
            for locallink in body.iter(NS.PyWebXML.a):
                locallink.tag = NS.XHTML.a
                self.transform_href(ctx, locallink)
        if img:
            for localimg in body.iter(NS.PyWebXML.img):
                localimg.tag = NS.XHTML.img
                self.transform_href(ctx, localimg)
                localimg.set("src", localimg.get("href"))
                del localimg.attrib["href"]
        if link:
            for locallink in body.iter(NS.PyWebXML.link):
                locallink.tag = NS.XHTML.link
                if locallink.get("href"):
                    self.transform_href(ctx, locallink)
        if mobile_switch:
            todelete = set()
            for mobile_switch in body.iter(getattr(NS.PyWebXML, "if-mobile")):
                if Types.Typecasts.bool(mobile_switch.get("mobile", True)) != ctx.IsMobileClient:
                    todelete.add(mobile_switch)
                    continue
                try:
                    xhtmlel = mobile_switch.attrib.pop("xhtml-element")
                except KeyError:
                    xhtmlel = "span"
                mobile_switch.tag = getattr(NS.XHTML, xhtmlel)
                try:
                    del mobile_switch.attrib["mobile"]
                except KeyError:
                    pass
            for mobile_switch in todelete:
                mobile_switch.getparent().remove(mobile_switch)
        if content_attr:
            content_attrname = NS.PyWebXML.content
            content_make_uri_attrname = getattr(NS.PyWebXML, "content-make-uri")
            for el in body.iterfind(".//*[@{0}]".format(content_attrname)):
                make_uri = el.get(content_make_uri_attrname)
                if make_uri is not None:
                    del el.attrib[content_make_uri_attrname]
                    make_global = Types.Typecasts.bool(make_uri)
                else:
                    make_global = False
                el.set("content", el.get(content_attrname))
                del el.attrib[content_attrname]
                self.transform_href(ctx, el, "content", make_global=make_global)


    def get_template_arguments(self, ctx):
        # XXX: This will possibly explode one day ...
        return {
            b"site_title": utils.unicode2xpathstr(self.title),
            b"mobile_client": "1" if ctx.IsMobileClient else "0"
        }

    def transform_relative_uri(self, ctx, uri, make_global=False):
        if uri is None or uri.startswith("/") or self.urn_scheme.search(uri):  # non local href
            return uri
        uri = os.path.join(self.urlroot, uri)
        if make_global:
            uri = "{0}://{1}{2}".format(ctx.URLScheme, ctx.HostName, uri)
        return uri

    def transform_href(self, ctx, node, attrname="href", make_global=False):
        """
        Transform the attribute *attrname* on the ETree node *node* as if it
        was a possibly local url. If it is local and relative, it gets
        transformed so that it points to the same location independent of the
        current URL.
        """
        v = node.get(attrname)
        node.set(attrname, self.transform_relative_uri(ctx, v, make_global=make_global))


    def _get_node(self, ctx):
        """
        Find the node pointed to by the *Path* stored in the Context *ctx*.
        """
        path = ctx.Path
        if len(path) > 0 and path[0] == "/":
            path = path[1:]
        try:
            node = self.tree.resolve_path(ctx, path)
        except Errors.InternalRedirect as redirect:
            ctx.Path = redirect.new_location
            return self._get_node(ctx)
        return node

    def add_crumb(self, crumb):
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

    def register_node_id(self, ID, node):
        """
        Nodes may have IDs under which they can be referred using the Site. This
        method is used to register the *node* under a given *ID*. This will
        raise a ValueError if the ID is duplicated.
        """
        self.nodes[ID] = node

    def unregister_node_id(self, ID):
        del self.nodes[ID]

    def get_node(self, ID):
        """
        Retrieve the node which has the ID *ID*.
        """
        return self.nodes[ID]

    def _setup_cache(self, key, cls, *args):
        """
        Setup a cache with *key* and class *cls* passing *args* to its
        constructor as a specialized Cache in our *cache* attribute.
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
        return self.cache.specialized_cache(key, cls, *args)

    def load_sitemap(self, sitemap_file):
        """
        Load the whole sitemap XML from *sitemap_file*.
        """
        # set this up for later auto-reload
        self.sitemap_file = sitemap_file
        self.sitemap_timestamp = utils.file_last_modified(sitemap_file)

        # parse the sitemap
        root = ET.parse(sitemap_file).getroot()

        # load metadata
        self._load_meta(root)

        # setup specialized caches
        self.template_cache = self._setup_cache((self, "templates"),
            Templates.XSLTTemplateCache, self.root)
        self.file_document_cache = self._setup_cache((self, "file-doc-cache"),
            Document.FileDocumentCache, self.root)
        self.xml_data_cache = self._setup_cache((self, "xml-data-cache"),
            Resource.XMLFileCache, self.root)
        self.parser_registry = Registry.ParserRegistry()
        self.tweak_registry = Registry.TweakRegistry()
        self.hooks = Registry.HookRegistry()

        # load plugins
        self._load_plugins(root)

        # instanciate sitletons, so they're ready when the tweaks come in
        self.sitletons = Registry.Sitletons.instanciate(self)

        # load extended configuration
        tweaks = root.find(NS.Site.tweaks)
        if tweaks is None:
            tweaks = ET.Element(NS.Site.tweaks)
        self._load_tweaks(tweaks)

        self.hooks.call("tweaks-loaded")

        # load site tree
        self._load_tree(root)

        self.hooks.call("tree-loaded")

        # setup the default template
        if self.default_template is None:
            self.default_template = self.tree.Template or "templates/default.xsl"

        # load crumbs
        self._load_crumbs(root)

        self.hooks.call("crumbs-loaded")
        self.hooks.call("loading-finished")
        logging.debug("Sitemap loaded successfully")

    def update(self):
        """
        If neccessary, reload the whole sitemap. Print a warning to the log, as
        this is still fragile.
        """
        sitemap_timestamp = utils.file_last_modified(self.sitemap_file)
        if sitemap_timestamp > self.sitemap_timestamp:
            logging.info("sitemap xml changed -- reloading COMPLETE site.")
            self.hooks.call("global-reload")
            # Registry.clear_all()
            # self.savepoint.rollback()
            self.load_sitemap(self.sitemap_file)

    def handle_not_found(self, ctx, resource_name):
        """
        Handle a NotFound exception if it occurs while traversing the sitetree
        in the search for a node to handle the current request.
        """
        try:
            tpl = self.template_cache[self.not_found_template]
        except Exception as err:
            warnings.warn(str(err))
            body = ET.Element(NS.XHTML.body)
            section = ET.SubElement(body, NS.XHTML.section)
            header = ET.SubElement(section, NS.XHTML.header)
            h2 = ET.SubElement(header, NS.XHTML.h2)
            h2.text = "Resource not found"
            p = ET.SubElement(section, NS.XHTML.p)
            p.text = "The resource {0} could not be found.".format(resource_name)
            p = ET.SubElement(section, NS.XHTML.p)
            p.text = "Additionally, the specified (or fallback) error template\
 at {0} could not be loaded: {1}.".format(self.not_found_template,
                type(err).__name__)
            return Document.Document("Not found", [], [], body)
        else:
            err = ET.Element(NS.PyWebXML.error, attrib={
                "type": "not-found"
            })
            ET.SubElement(err, NS.PyWebXML.resource).text = resource_name
            return tpl.transform(err, {})

    def get_message(self, ctx):
        """
        Handle a request in the given Context *ctx*.
        """
        # mark ourselves as a used resource
        ctx.use_resource(self)

        # call a hook used by some tweaks
        self.hooks.call("handle.pre-lookup", ctx)

        # prepare iterable with loaded html transformations
        html_transforms = itertools.imap(self.template_cache.__getitem__, \
            self.html_transforms)

        # default status code
        status = Errors.OK
        try:
            # attempt lookup
            node = self._get_node(ctx)
        except Errors.NotFound as status:
            if status.document is not None:
                data = status.document
                template = status.template
            else:
                data = self.handle_not_found(ctx,
                        status.resource_name or ctx.Path)
                template = None
            if template is None:
                template = self.template_cache[self.default_template]
        else:
            # setup the context
            ctx._pagenode = node
            # load the template and mark it for use
            template = self.template_cache[node.Template]
            ctx.use_resource(template)

            # evaluate the iterable as we need the list multiple times in this
            # code path
            html_transforms = list(html_transforms)
            ctx.use_resources(html_transforms)

            content_type = node.get_content_type(ctx)
            if content_type == ContentTypes.xhtml:
                if not ctx.HTML5Support and self.html4_transform:
                    ctx.use_resource(self.template_cache[self.html4_transform])
            if not ctx.CanUseXHTML:
                # we'll do conversion later
                content_type = ContentTypes.html
            ctx.check_acceptable(content_type)

            # raise NotModified if the result will be available on the client
            # side
            ctx.check_not_modified()

            # otherwise, create the document and return it
            data = node.handle(ctx)

        if isinstance(data, Document.Document):
            # do the final transformation on the content fetched from the node
            result_tree = template.final(ctx, data,
                    license_fallback=self._license)

            for xslt in html_transforms:
                result_tree = xslt.raw_transform(result_tree, {})

            if not ctx.HTML5Support and self.html4_transform:
                transform = self.template_cache[self.html4_transform]
                result_tree = transform.raw_transform(result_tree, {})

            if not ctx.CanUseXHTML:
                message = Message.HTMLMessage.from_xhtml_tree(result_tree,
                    status=status, encoding="utf-8",
                    pretty_print=self.pretty_print
                )
            else:
                message = Message.XHTMLMessage(result_tree,
                    status=status, encoding="utf-8",
                    pretty_print=self.pretty_print,
                    force_namespaces=dict(self._force_namespaces)
                )
        elif isinstance(data, (ET._Element, ET._ElementTree)):
            message = Message.XMLMessage(data, content_type,
                status=status, encoding="utf-8",
                cleanup_namespaces=True, pretty_print=self.pretty_print
            )
        elif isinstance(data, basestring):
            message = Message.TextMessage(data, content_type,
                status=status, encoding="utf-8"
            )
        else:
            raise TypeError("Cannot process node result: {0}".format(type(data)))
        # only enforce at the end of a request, otherwise things may become
        # horribly slow if more resources are needed than the cache allows
        self.cache.enforce_limit()
        return message

    def handle(self, ctx):
        try:
            return self.get_message(ctx)
        except Errors.Handler.InternalServerError as err:
            return Message.HTMLMessage.from_xhtml_tree(err.xhtml, status=Errors.HTTP500,
                encoding="utf-8")
        except Errors.MethodNotAllowed as status:
            ctx.Cachable = False
            ctx.set_response_header("allow", ",".join(status.allow))
            raise
        except Errors.HTTPStatusBase:
            raise
        except Exception as err:
            xhtml = Errors.Handler.InternalServerError(ctx, *sys.exc_info()).xhtml
            return Message.HTMLMessage.from_xhtml_tree(xhtml, status=Errors.HTTP500,
                encoding="utf-8")
