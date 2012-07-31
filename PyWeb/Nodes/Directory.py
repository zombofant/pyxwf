import itertools

from PyWeb.utils import ET

import PyWeb.Errors as Errors

import PyWeb.Registry as Registry
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation

class Directory(Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    class NavigationInfo(Navigation.Info):
        def __init__(self, ctx, directory):
            self.children = directory.children
            self.display = directory.display
            self.index = directory.index
            self.superInfo = self.index.getNavigationInfo(ctx)

        def getTitle(self):
            return self.superInfo.getTitle()

        def getDisplay(self):
            return self.display

        def getRepresentative(self):
            return self.index

        def __iter__(self):
            try:
                superIter = iter(self.superInfo)
            except (ValueError, TypeError):
                superIter = iter([])
            return iter(itertools.chain(
                iter(superIter),
                itertools.ifilter(lambda x: x is not self.index, self.children)
            ))

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/directory"
    names = ["node"]
    
    def __init__(self, site, parent, node):
        super(Directory, self).__init__(site, parent, node)
        self.pathDict = {}
        self.children = []
        self.display = Navigation.DisplayMode(node.get("nav-display"),
            default=Navigation.Show)
        for child in node:
            if child.tag is ET.Comment:
                continue
            self.append(Registry.NodePlugins(child, site, self))
        try:
            self.index = self.pathDict[""]
        except KeyError:
            raise ValueError("Directory requires index node (i.e. child node with unset or empty name)")

    def append(self, plugin):
        if plugin.Name in self.pathDict:
            raise ValueError("Duplicate path name: {0}".format(plugin.name))
        self.pathDict[plugin.Name] = plugin
        self.children.append(plugin)

    def resolvePath(self, fullPath, relPath):
        if fullPath[-1:] != "/" and len(relPath) == 0 and len(fullPath) > 0:
            raise Errors.Found(newLocation=fullPath+"/")
        try:
            pathHere, relPath = relPath.split("/", 1)
        except ValueError:
            pathHere = relPath
            relPath = ""
        node = self.pathDict.get(pathHere, None)
        if node is None:
            raise Errors.NotFound()
        return node.resolvePath(fullPath, relPath)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def getNavigationInfo(self, ctx):
        return self.NavigationInfo(ctx, self)

class RootDirectory(Directory):
    __metaclass__ = Registry.NodeMeta
    
    namespace = Directory.namespace
    names = ["tree"]
