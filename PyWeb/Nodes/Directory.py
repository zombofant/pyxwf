from PyWeb.utils import ET

import PyWeb.Errors as Errors

import PyWeb.Registry as Registry
import PyWeb.Nodes as Nodes

class Directory(Nodes.Node):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyweb.zombofant.net/xmlns/nodes/directory"
    
    def __init__(self, parent, tag, node, site):
        super(Directory, self).__init__(parent, tag, node, site)
        self.pathDict = {}
        self.children = []
        for child in node:
            if child.tag is ET.Comment:
                continue
            self.append(Registry.NodePlugins.getPluginInstance(child, self, site))

    def append(self, plugin):
        if plugin.name in self.pathDict:
            raise ValueError("Duplicate path name: {0}".format(plugin.name))
        self.pathDict[plugin.name] = plugin
        self.children.append(plugin)

    def getDocument(self):
        pass

    def resolvePath(self, fullPath, relPath):
        try:
            pathHere, relPath = relPath.split("/", 1)
        except ValueError:
            pathHere = relPath
            relPath = ""
        node = self.pathDict.get(pathHere, None)
        if node is None:
            raise Errors.NotFound(resourceName=fullPath)
        return node.resolvePath(fullPath, relPath)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)
