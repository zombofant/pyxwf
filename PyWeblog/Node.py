from __future__ import unicode_literals, print_function, absolute_import

import operator
import itertools
import logging

from PyXWF.utils import ET, blist, _F
import PyXWF.utils as utils
import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types

import PyWeblog.Protocols as Protocols
import PyWeblog.Index as Index
import PyWeblog.Directories as Directories

logger = logging.getLogger(__name__)

class Tweak(object):
    def __init__(self, site, parent, node):
        if not isinstance(parent, Blog):
            raise Errors.BadParent(self, parent)
        super(Tweak, self).__init__()
        self.site = site
        self.Parent = parent
        self.Blog = parent

class Blog(Nodes.DirectoryResolutionBehaviour, Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["node"]

    _child_order_type = Types.DefaultForNone(True,
        Types.EnumMap({
            "posts+static": True,
            "static+posts": False
        })
    )
    _structure_type = Types.EnumMap({
        # "year/month": True,
        "year+month": False
    })

    class Info(Navigation.Info):
        def __init__(self, blog, ctx):
            self.blog = blog
            self.landing_page = self.blog._landing_page
            self.super_info = self.landing_page.get_navigation_info(ctx)

        def get_title(self):
            return self.super_info.get_title()

        def get_representative(self):
            return self.super_info.get_representative()

        def get_display(self):
            self.blog._navdisplay

        def __iter__(self):
            if self.blog._posts_first:
                return itertools.chain(
                    self.blog._post_containers,
                    self.blog._childnode_list
                )
            else:
                return itertools.chain(
                    self.blog._childnode_list,
                    self.blog._post_containers
                )

        def __len__(self):
            return len(self.blog._childnode_list) + len(self.blog._post_containers)

    def __init__(self, site, parent, node):
        super(Blog, self).__init__(site, parent, node)
        self._childnodes = {}
        self._childnode_list = []
        self._post_containers = blist.sortedlist(key=lambda x: -x.year)
        self._tweaks = []
        self._year_nodes = {}

        # some plugin hook points. These are accessible via their respective
        # properties, see their documentation for more details
        self._tag_dir = None
        self._feeds = None

        self._navdisplay = Navigation.DisplayMode(node.get("nav-display", "show"))
        self._posts_first = self._child_order_type(node.get("child-order"))
        self._nest_months = self._structure_type(node.get("structure"))

        self.month_template = Types.NotNone(node.get("month-template"))
        self.post_template = Types.NotNone(node.get("post-template"))
        self.show_posts_in_nav = Types.Typecasts.bool(node.get("show-posts-in-nav", True))

        entry_dir = Types.NotNone(node.get("entry-dir"))
        self.index = Index.Index(self, site.file_document_cache, entry_dir,
            self.Path + "{year}/{month}/{basename}",
            self.site.long_date_format,
            posts_changed_callback=self._posts_changed)
        self.index._reload()

        self._load_children(node)
        try:
            self._landing_page = self._childnodes[""]
        except KeyError:
            raise Errors.NodeConfigurationError(\
                "Blog requires landing page (child node with empty name)", self)

    def _add_child(self, plugin):
        name = plugin.Name
        try:
            int(name)
        except ValueError:
            # valid name, but not an integer, that's fine
            pass
        except TypeError:
            raise Errors.NodeConfigurationError(\
                "Blog children must not ".format(plugin.Name), self)
        else:
            raise Errors.NodeConfigurationError(\
                "Conflict: Blog children cannot have names which are parsable \
                as an integer: {0}.".format(plugin.Name), self)
        if name in self._childnodes:
            raise Errors.NodeNameConflict(self, plugin, name,
                    self._childnodes[name])
        self._childnodes[name] = plugin
        self._childnode_list.append(plugin)

    def _autocreate_year_node(self, year):
        year = int(year)
        try:
            return self._year_nodes[year]
        except KeyError:
            node = Directories.YearDir(self, year)
            self._year_nodes[year] = node
            self._post_containers.add(node)
            return node

    def resolve_path(self, ctx, relpath):
        ctx.use_resource(self.index)
        return super(Blog, self).resolve_path(ctx, relpath)

    def _get_child(self, key):
        try:
            year = int(key)
        except ValueError:
            try:
                return self._childnodes[key]
            except KeyError:
                return None
        else:
            return self._year_nodes[year]

    def _load_children(self, node):
        # this must only run on a fresh blog node
        assert not self._tweaks
        assert not self._childnodes

        site = self.site
        for child in node:
            if child.tag is ET.Comment:
                continue
            plugin = Registry.NodePlugins.get(child, site, self)
            if isinstance(plugin, Tweak):
                self._tweaks.append(plugin)
            else:
                self._add_child(plugin)

    def _posts_changed(self):
        logger.debug("Posts changed callback")
        known_years = set(map(operator.attrgetter("year"), self._year_nodes.viewvalues()))
        curr_years = set()
        for year, monthiter in self.index.iter_deep():
            yearnode = self._autocreate_year_node(year)
            for month in monthiter:
                monthnode = yearnode.autocreate_month_node(month)
            yearnode.purge_empty()
            curr_years.add(year)

        deleted = known_years - curr_years
        for deleted_year in deleted:
            node = self._year_nodes.pop(deleted_year)
            self._post_containers.remove(node)

        try:
            callable = self._tag_dir.update_children
        except AttributeError:
            pass
        else:
            callable()

    @property
    def TagDirectory(self):
        """
        Store a reference to the :class:`~PyWeblog.TagDir.TagDirBase` instance
        to be used by this blog instance. This should be set by the respective
        :class:`~PyWeblog.TagDir.TagDirBase` instance upon initialization and
        will be used by the blog to create links to tag pages.
        """
        return self._tag_dir

    @TagDirectory.setter
    def TagDirectory(self, value):
        if not isinstance(value, Protocols.TagDir):
            raise TypeError("TagDirectory must implement TagDir protocol.")
        logger.debug(_F("Blog was assigned a new tag dir: {0}", value))
        self._tag_dir = value
        if self._tag_dir is not None:
            self._tag_dir.update_children()

    @property
    def Feeds(self):
        """
        A provider class for feeds like Atom, RSS and so on. Such a class must
        implement the FeedBase protocol. This property will be set automatically
        by the respective objects upon creation, i.e. when they're encountered
        in the sitemap.
        """
        return self._feeds

    @Feeds.setter
    def Feeds(self, value):
        if not isinstance(value, Protocols.Feeds):
            raise TypeError("Feeds must implement Feeds protocol.")
        logger.debug(_F("Blog was assigned a new feed provider: {0}", value))
        self._feeds = value

    def get_transform_args(self):
        args = {}
        try:
            args[b"tag-root"] = utils.unicode2xpathstr(self._tag_dir.Path)
        except AttributeError:
            args[b"tag-root"] = "0"
        return args

    def get_navigation_info(self, ctx):
        return self.Info(self, ctx)
