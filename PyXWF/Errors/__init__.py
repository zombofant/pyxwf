from HTTP import *
import Handler
import PyXWF.utils as utils

import os

class InternalRedirect(Exception):
    def __init__(self, to):
        self.to = to

class MalformedHTTPRequest(ValueError):
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
        ns, name = utils.split_tag(tag)
        super(MissingTweakPlugin, self).__init__(ns, name,
            "No plugin for tweak {{{0}}}{1}"
        )

class PluginConflict(Exception):
    def __init__(self, key, plugin1, plugin2, objstr=None):
        super(PluginConflict, self).__init__(
            "Conflict: {0} is shared by both {1} and {2}".format(
                objstr or key, plugin1, plugin2
            )
        )
        self.key = key
        self.plugin1 = plugin1
        self.plugin2 = plugin2

class CacheConflict(Exception):
    def __init__(self, key):
        self.key = key
        super(CacheConflict, self).__init__(
            "Attempt to register two sub-caches for cache key {0}".format(
                key
            )
        )

class ResourceLost(Exception):
    def __init__(self, filename):
        basename = os.path.basename(filename)
        super(ResourceLost, self).__init__(
            "Resource at {0} cannot be found anymore.".format(basename)
        )
        self.path = filename

class UnknownMIMEType(Exception):
    def __init__(self, filename):
        basename = os.path.basename(filename)
        super(UnknownMIMEType, self).__init__(
            "No idea what type that file is: {0}".format(basename)
        )
        self.path = filename

class ConfigurationError(Exception):
    def __init__(self, message):
        super(ConfigurationError, self).__init__(message)

class CrumbConfigurationError(ConfigurationError):
    def __init__(self, message, crumb):
        self.crumb = crumb
        super(CrumbConfigurationError, self).__init__(message)

class NodeConfigurationError(ConfigurationError):
    def __init__(self, message, node):
        self.node = node
        super(NodeConfigurationError, self).__init__(message)

class NodeNameConflict(ConfigurationError):
    def __init__(self, parent, child, name, other=None):
        self.parent = parent
        self.child = child
        self.name = name
        self.other = other
        if other is not None:
            self.message = "Name {0!r} of node {1} in {2} conflicts with {3}".\
                format(
                    name,
                    child,
                    parent,
                    other
                )
        else:
            self.message = "Name {0!r} of node {1} in {2} conflicts with \
                            existing node".\
                format(
                    name,
                    child,
                    parent
                )
        super(NodeNameConflict, self).__init__(message)

class BadParent(NodeConfigurationError):
    def __init__(self, node, parent):
        self.child = node
        self.parent = parent
        super(BadParent, self).__init__(
            "{0} is not a valid parent for {1}".format(self.parent, self.child),
            self.parent
        )

class BadChild(NodeConfigurationError):
    def __init__(self, node, parent):
        self.child = node
        self.parent = parent
        super(BadChild, self).__init__(
            "{1} is not a valid child for {0}".format(self.parent, self.child),
            self.parent
        )

class SitletonNotAvailable(Exception):
    def __init__(self, cls, site):
        self.sitleton_class = cls
        self.site = site
        super(SitletonNotAvailable, self).__init__(
            "Sitleton {0} is not available at site {1}".format(cls, site)
        )
