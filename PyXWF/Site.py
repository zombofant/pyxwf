# encoding=utf-8
# File name: Site.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
"""
The heart of PyXWF is beating in the :class:`~Site` instance. It accepts requests
and passes them through the tree defined in the sitemap xml.
"""
from __future__ import unicode_literals

import itertools
import os
import importlib
import copy
import mimetypes
import warnings
import re
import sys
import logging
import platform

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

import PyXWF.Tweaks.CoreTweaks

logger = logging.getLogger(__name__)

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
        logger.info(_F(
"Initializing PyXWF/{pyxwf_version} at {pid} with {python}/{python_version} lxml.etree/{etree_version}, {threading}, blist/{blist_version}",
            pyxwf_version=PyXWF.__version__,
            etree_version=ET.__version__,
            threading=threading.__name__,
            blist_version=blist.__version__,
            pid=os.getpid(),
            python=platform.python_implementation(),
            python_version=platform.python_version()
        ))
        super(Site, self).__init__(**kwargs)
        self.startcwd = os.getcwd()
        self.default_url_root = default_url_root
        self.final_transform = Templates.XSLTTemplate(
            self,
            os.path.join(PyXWF.data_path, "final-transform.xsl")
        )
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

    def _load_tweaks(self, tweaks):
        """
        Load extended configuration (called tweaks).
        """
        # further information, warn about unknown tags in our namespace
        for child in tweaks:
            if child.tag is ET.Comment:
                continue
            ns, name = utils.split_tag(child.tag)
            try:
                self.tweak_registry.submit_tweak(child)
            except Errors.MissingTweakPlugin as err:
                logger.warning(unicode(err))

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
        for i, node in enumerate(crumb.render(ctx, parent)):
            parent.insert(idx+i, node)

    def _load_optional_transformations(self):
        if self.remove_xhtml_prefixes:
            self.prefixless_xhtml = Templates.XSLTTemplate(
                self,
                os.path.join(PyXWF.data_path, "prefixless-xhtml.xsl")
            )
        else:
            self.prefixless_xhtml = None


    def transform_py_namespace(self, ctx, body, crumbs=True):
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
        return self.final_transform.raw_transform(
            body,
            self.get_template_arguments(ctx)
        ).getroot()


    def get_template_arguments(self, ctx):
        # XXX: This will possibly explode one day ...
        return {
            b"site_title": utils.unicode2xpathstr(self.title),
            b"deliver_mobile": "1" if ctx.IsMobileClient else "0",
            b"mobile_client": "1" if ctx.IsMobileClient else "0",
            b"host_name": utils.unicode2xpathstr(ctx.HostName),
            b"url_scheme": utils.unicode2xpathstr(ctx.URLScheme),
            b"url_root": utils.unicode2xpathstr(self.urlroot),
            b"full_uri": utils.unicode2xpathstr(ctx.FullURI)
        }

    def transform_relative_uri(self, ctx, uri, make_global=False):
        if uri is None or self.urn_scheme.search(uri):  # non local href
            return uri or ""
        if uri.startswith("/"):
            if not make_global:
                return uri
        else:
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

        # reinitialize cache
        self.cache = Cache.Cache(self)

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
        logger.debug("Sitemap loaded successfully, executing post-config")

        self._load_optional_transformations()

    def update(self):
        """
        If neccessary, reload the whole sitemap. This works as long as the new
        sitemap does not depend on any python code changes.
        """
        sitemap_timestamp = utils.file_last_modified(self.sitemap_file)
        if sitemap_timestamp > self.sitemap_timestamp:
            logger.info("sitemap xml changed -- reloading complete site.")
            self.hooks.call("global-reload")
            self.load_sitemap(self.sitemap_file)

    def handle_not_found(self, ctx, resource_name):
        """
        Handle a NotFound exception if it occurs while traversing the sitetree
        in the search for a node to handle the current request.
        """
        try:
            tpl = self.template_cache[self.not_found_template]
            ctx.use_resource(tpl)
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
            logger.debug("dispatching request")
            node = self._get_node(ctx)
        except Errors.NotFound as status:
            logger.debug("no target node found, generating error page")
            if status.document is not None:
                data = status.document
                template = status.template
            else:
                data = self.handle_not_found(ctx,
                        status.resource_name or ctx.Path)
                template = None
            if template is None:
                template = self.template_cache[self.default_template]
                ctx.use_resource(template)
        else:
            logger.debug("preparing context")
            # setup the context
            ctx.PageNode = node

            logger.debug("load & announce template")
            # load the template and mark it for use
            template_path = node.Template or self.default_template
            if template_path is None:
                raise ValueError("no valid template -- neither node nor default template is properly set.")
            template = self.template_cache[template_path]
            ctx.use_resource(template)

            logger.debug("load & announce transformations")
            # evaluate the iterable as we need the list multiple times in this
            # code path
            html_transforms = list(html_transforms)
            ctx.use_resources(html_transforms)

            logger.debug("checking content type")
            content_type = node.get_content_type(ctx)
            if content_type == ContentTypes.xhtml:
                if not ctx.HTML5Support and self.html4_transform:
                    ctx.use_resource(self.template_cache[self.html4_transform])
            if self.disable_xhtml:
                ctx.CanUseXHTML = False
                logger.debug("XHTML disabled in config")
            if not ctx.CanUseXHTML:
                # we'll do conversion later
                content_type = ContentTypes.html
            ctx.check_acceptable(content_type)

            if self.client_cache:
                logger.debug("probing for cache early out")
                # raise NotModified if the result is already known to
                # the client (as per If-Modified-Since header)
                ctx.check_not_modified()
            else:
                # no client-side caching allowed.
                logger.debug("client side caching disabled")

            logger.debug("asking node for document to return")
            # otherwise, create the document and return it
            data = node.handle(ctx)

        if isinstance(data, Document.Document):
            logger.debug("got Document, rendering")
            # do the final transformation on the content fetched from the node
            result_tree = template.final(ctx, data,
                    license_fallback=self._license)

            logger.debug("performing additional transformations")
            for xslt in html_transforms:
                result_tree = xslt.raw_transform(result_tree, {})

            if not ctx.HTML5Support and self.html4_transform:
                logger.debug("xhtml5->xhtml1 transformation")
                transform = self.template_cache[self.html4_transform]
                result_tree = transform.raw_transform(result_tree, {})

            if not ctx.CanUseXHTML:
                logger.debug("xhtml->html transformation & pass result")
                message = Message.HTMLMessage.from_xhtml_tree(result_tree,
                    status=status, encoding="utf-8",
                    pretty_print=self.pretty_print
                )
            else:
                logger.debug("pass result")
                if not ctx.PrefixedXHTMLSupport and self.remove_xhtml_prefixes:
                    logger.debug("Client is unable to deal with prefixed XHTML, performing transform")
                    result_tree = self.prefixless_xhtml.raw_transform(
                        result_tree,
                        {}
                    )

                message = Message.XHTMLMessage(result_tree,
                    status=status, encoding="utf-8",
                    pretty_print=self.pretty_print,
                    force_namespaces=dict(self.force_namespaces)
                )
        elif isinstance(data, (ET._Element, ET._ElementTree)):
            logger.debug("got Element(Tree)?, returning XML document")
            message = Message.XMLMessage(data, content_type,
                status=status, encoding="utf-8",
                cleanup_namespaces=True, pretty_print=self.pretty_print
            )
        elif isinstance(data, basestring):
            logger.debug("got string, returning plain text")
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
