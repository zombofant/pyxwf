from __future__ import unicode_literals, print_function, absolute_import

import operator, itertools, logging

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

class Tweak(object):
    def __init__(self, site, parent, node):
        if not isinstance(parent, Blog):
            raise Errors.BadParent(self, parent)
        super(Tweak, self).__init__()
        self.Site = site
        self.Parent = parent
        self.Blog = parent

class Blog(Nodes.DirectoryResolutionBehaviour, Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["node"]

    _childOrderType = Types.DefaultForNone(True,
        Types.EnumMap({
            "posts+static": True,
            "static+posts": False
        })
    )
    _structureType = Types.EnumMap({
        # "year/month": True,
        "year+month": False
    })

    class Info(Navigation.Info):
        def __init__(self, blog, ctx):
            self.blog = blog
            self.landingPage = self.blog._landingPage
            self.superInfo = self.landingPage.getNavigationInfo(ctx)

        def getTitle(self):
            return self.superInfo.getTitle()

        def getRepresentative(self):
            return self.superInfo.getRepresentative()

        def getDisplay(self):
            self.blog._navDisplay

        def __iter__(self):
            if self.blog._postsFirst:
                return itertools.chain(
                    self.blog._postContainers,
                    self.blog._childNodeList
                )
            else:
                return itertools.chain(
                    self.blog._childNodeList,
                    self.blog._postContainers
                )

        def __len__(self):
            return len(self.blog._childNodeList) + len(self.blog._postContainers)

    def __init__(self, site, parent, node):
        super(Blog, self).__init__(site, parent, node)
        self._childNodes = {}
        self._childNodeList = []
        self._postContainers = blist.sortedlist(key=lambda x: -x.year)
        self._tweaks = []
        self._yearNodes = {}

        # some plugin hook points. These are accessible via their respective
        # properties, see their documentation for more details
        self._tagDir = None
        self._feeds = None

        self._navDisplay = Navigation.DisplayMode(node.get("nav-display", "show"))
        self._postsFirst = self._childOrderType(node.get("child-order"))
        self._nestMonths = self._structureType(node.get("structure"))

        self.monthTemplate = Types.NotNone(node.get("month-template"))
        self.postTemplate = Types.NotNone(node.get("post-template"))
        self.showPostsInNav = Types.Typecasts.bool(node.get("show-posts-in-nav", True))

        entryDir = Types.NotNone(node.get("entry-dir"))
        self.index = Index.Index(self, site.fileDocumentCache, entryDir,
            self.Path + "{year}/{month}/{basename}",
            self.Site.longDateFormat,
            postsChangedCallback=self._postsChanged)
        self.index._reload()

        self._loadChildren(node)
        try:
            self._landingPage = self._childNodes[""]
        except KeyError:
            raise Errors.NodeConfigurationError(\
                "Blog requires landing page (child node with empty name)", self)

    def _addChild(self, plugin):
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
        if name in self._childNodes:
            raise Errors.NodeNameConflict(self, plugin, name,
                    self._childNodes[name])
        self._childNodes[name] = plugin
        self._childNodeList.append(plugin)

    def _autocreateYearNode(self, year):
        year = int(year)
        try:
            return self._yearNodes[year]
        except KeyError:
            node = Directories.YearDir(self, year)
            self._yearNodes[year] = node
            self._postContainers.add(node)
            return node

    def resolvePath(self, ctx, relPath):
        ctx.useResource(self.index)
        return super(Blog, self).resolvePath(ctx, relPath)

    def _getChildNode(self, key):
        try:
            year = int(key)
        except ValueError:
            try:
                return self._childNodes[key]
            except KeyError:
                return None
        else:
            return self._yearNodes[year]

    def _loadChildren(self, node):
        # this must only run on a fresh blog node
        assert not self._tweaks
        assert not self._childNodes

        site = self.Site
        for child in node:
            if child.tag is ET.Comment:
                continue
            plugin = Registry.NodePlugins.getPluginInstance(child, site, self)
            if isinstance(plugin, Tweak):
                self._tweaks.append(plugin)
            else:
                self._addChild(plugin)

    def _postsChanged(self):
        logging.debug("Posts changed callback")
        knownYears = set(map(operator.attrgetter("year"), self._yearNodes.viewvalues()))
        currYears = set()
        for year, monthIter in self.index.iterDeep():
            yearNode = self._autocreateYearNode(year)
            for month in monthIter:
                monthNode = yearNode.autocreateMonthNode(month)
            yearNode.purgeEmpty()
            currYears.add(year)

        deleted = knownYears - currYears
        for deletedYear in deleted:
            node = self._yearNodes.pop(deletedYear)
            self._postContainers.remove(node)

        try:
            callable = self._tagDir.updateChildren
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
        return self._tagDir

    @TagDirectory.setter
    def TagDirectory(self, value):
        if not isinstance(value, Protocols.TagDir):
            raise TypeError("TagDirectory must implement TagDir protocol.")
        logging.debug(_F("Blog was assigned a new tag dir: {0}", value))
        self._tagDir = value
        if self._tagDir is not None:
            self._tagDir.updateChildren()

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
        logging.debug(_F("Blog was assigned a new feed provider: {0}", value))
        self._feeds = value

    def getTransformArgs(self):
        args = {}
        try:
            args[b"tag-root"] = utils.unicodeToXPathStr(self._tagDir.Path + "/")
        except AttributeError:
            args[b"tag-root"] = "0"
        return args

    def getNavigationInfo(self, ctx):
        return self.Info(self, ctx)
