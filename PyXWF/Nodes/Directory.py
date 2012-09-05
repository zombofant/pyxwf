import itertools

from PyXWF.utils import ET

import PyXWF.Errors as Errors

import PyXWF.Registry as Registry
import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation

class DirectoryBase(Nodes.DirectoryResolutionBehaviour, Nodes.Node):

    class Info(Navigation.Info):
        def __init__(self, ctx, directory):
            self.children = directory.children
            self.display = directory.display
            self.index = directory.index
            self.super_info = self.index.get_navigation_info(ctx)

        def get_title(self):
            return self.super_info.get_title()

        def get_display(self):
            return self.display

        def get_representative(self):
            return self.index

        def __iter__(self):
            try:
                superiter = iter(self.super_info)
            except (ValueError, TypeError):
                superiter = iter([])
            return iter(itertools.chain(
                iter(superiter),
                itertools.ifilter(lambda x: x is not self.index, self.children)
            ))

    def __init__(self, site, parent, node):
        super(DirectoryBase, self).__init__(site, parent, node)
        self.pathdict = {}
        self.children = []
        self.display = Navigation.DisplayMode(
            node.get("nav-display", Navigation.Show) if node is not None else Navigation.Show)

    def _load_children(self, from_node):
        site = self.Site
        for child in from_node:
            if child.tag is ET.Comment:
                continue
            self.append(Registry.NodePlugins(child, site, self))
        try:
            self.index = self.pathdict[""]
        except KeyError:
            raise ValueError("Directory requires index node (i.e. child node with unset or empty name)")

    def _get_child(self, key):
        return self.pathdict.get(key, None)

    def append(self, plugin):
        if plugin.Name in self.pathdict:
            raise ValueError("Duplicate path name {0!r} in {1}".format(plugin.Name, self.Path))
        self.pathdict[plugin.Name] = plugin
        self.children.append(plugin)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def get_navigation_info(self, ctx):
        return self.Info(ctx, self)

class Directory(DirectoryBase):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyxwf.zombofant.net/xmlns/nodes/directory"
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Directory, self).__init__(site, parent, node)
        self._load_children(node)

class RootDirectory(Directory):
    __metaclass__ = Registry.NodeMeta

    namespace = Directory.namespace
    names = ["tree"]

    def __init__(self, site, parent, node):
        super(RootDirectory, self).__init__(site, parent, node)

    @property
    def Path(self):
        return None
