from HTTP import *

class InternalRedirect(Exception):
    def __init__(self, to):
        self.to = to

class MalformedHTTPRequset(ValueError):
    pass


class MissingPlugin(Exception):
    pass

class MissingDocumentPlugin(MissingPlugin):
    def __init__(self, mime):
        msg = "No Document handler for MIME type: {0}".format(mime)
        super(MissingDocumentPlugin, self).__init__(msg)
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
    def __init__(self, ns, name):
        super(MissingTweakPlugin, self).__init__(ns, name,
            "No plugin for tweak {{{0}}}{1}"
        )

