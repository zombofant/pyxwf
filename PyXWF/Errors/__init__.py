from HTTP import *
import Handler
import PyXWF.utils as utils

import os

class InternalRedirect(Exception):
    def __init__(self, to):
        self.to = to

class MalformedHTTPRequset(ValueError):
    pass


class MissingPlugin(Exception):
    pass

class MissingParserPlugin(MissingPlugin):
    def __init__(self, mime):
        msg = "No parser for MIME type: {0}".format(mime)
        super(MissingParserPlugin, self).__init__(msg)
        self.mime = mime

class MissingNamespacePlugin(MissingPlugin):
    def __init__(self, ns, name, fmt):
        self.ns = ns
        self.name = name
        super(MissingNamespacePlugin, self).__init__(
            fmt.format(ns, name)
        )

class MissingNodePlugin(MissingNamespacePlugin):
    def __init__(self, ns, name):
        super(MissingNodePlugin, self).__init__(ns, name,
            "No plugin for node {{{0}}}{1}"
        )

class MissingCrumbPlugin(MissingNamespacePlugin):
    def __init__(self, ns, name):
        super(MissingNodePlugin, self).__init__(ns, name,
            "No plugin for crumb {{{0}}}{1}"
        )

class MissingTweakPlugin(MissingNamespacePlugin):
    def __init__(self, tag):
        ns, name = utils.splitTag(tag)
        super(MissingTweakPlugin, self).__init__(ns, name,
            "No plugin for tweak {{{0}}}{1}"
        )

class PluginConflict(Exception):
    def __init__(self, key, plugin1, plugin2, objStr=None):
        super(PluginConflict, self).__init__(
            "Conflict: {0} is shared by both {1} and {2}".format(
                objStr or key, plugin1, plugin2
            )
        )
        self.key = key
        self.plugin1 = plugin1
        self.plugin2 = plugin2

class ResourceLost(Exception):
    def __init__(self, fileName):
        basename = os.path.basename(fileName)
        super(ResourceLost, self).__init__(
            "Resource at {0} cannot be found anymore.".format(basename)
        )
        self.path = fileName

class UnknownMIMEType(Exception):
    def __init__(self, fileName):
        basename = os.path.basename(fileName)
        super(UnknownMIMEType, self).__init__(
            "No idea what type that file is: {0}".format(basename)
        )
        self.path = fileName
