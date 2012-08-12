import os

import PyWeb.Errors as Errors

import PyWeb.Nodes as Nodes
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation

class RedirectBase(Nodes.Node):
    namespace = "http://pyweb.zombofant.net/xmlns/nodes/redirect"

    methods = {
        "found": Errors.Found,
        "see-other": Errors.SeeOther,
        "moved-permanently": Errors.MovedPermanently,
        "temporary-redirect": Errors.TemporaryRedirect,
        "internal": Errors.InternalRedirect
    }
    defaultMethod = "found"

    def __init__(self, site, parent, node):
        super(RedirectBase, self).__init__(site, parent, node)
        self.method = self.methods[node.get("method", self.defaultMethod)]

    def redirect(self, ctx):
        raise self.method(self.Target)

    def resolvePath(self, ctx, relPath):
        if relPath != "":
            raise Errors.NotFound(resource=fullPath)
        if self.method is Errors.InternalRedirect:
            raise self.method(self.Target)
        else:
            return self

    requestHandlers = redirect

class RedirectInternal(RedirectBase):
    __metaclass__ = Registry.NodeMeta

    namespace = RedirectBase.namespace
    names = ["internal"]

    class NavigationInfo(Navigation.Info):
        def __init__(self, ctx, redirect):
            self.redirect = redirect
            self.superInfo = redirect.TargetNode.getNavigationInfo(ctx)
            self.display = redirect.navDisplay
            self.title = redirect.navTitle or self.superInfo.getTitle()

        def getTitle(self):
            return self.title

        def getDisplay(self):
            return self.display

        def getRepresentative(self):
            return self.redirect


    def __init__(self, site, parent, node):
        super(RedirectInternal, self).__init__(site, parent, node)
        self.to = node.get("to")
        self.navTitle = node.get("nav-title")
        self.navDisplay = Navigation.DisplayMode(node.get("nav-display"),
            default=Navigation.Show)

    @property
    def TargetNode(self):
        if hasattr(self, "targetNode"):
            return self.targetNode
        else:
            self.targetNode = self.site.getNode(self.to)
            return self.targetNode

    @property
    def Target(self):
        return self.TargetNode.Path

    def getNavigationInfo(self, ctx):
        return self.NavigationInfo(ctx, self)
