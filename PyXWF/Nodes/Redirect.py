import os

import PyXWF.Errors as Errors

import PyXWF.Nodes as Nodes
import PyXWF.Registry as Registry
import PyXWF.Navigation as Navigation
import PyXWF.Types as Types
import PyXWF.Namespaces as NS

class RedirectNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/nodes/redirect"

class RedirectBase(Nodes.Node):
    namespace = str(RedirectNS)

    methods = {
        "found": Errors.Found,
        "see-other": Errors.SeeOther,
        "moved-permanently": Errors.MovedPermanently,
        "temporary-redirect": Errors.TemporaryRedirect,
        "internal": Errors.InternalRedirect
    }
    default_method = "found"

    def __init__(self, site, parent, node):
        super(RedirectBase, self).__init__(site, parent, node)
        self.method = self.methods[node.get("method", self.default_method)]
        self.cachable = Types.Typecasts.bool(node.get("cachable", True))

    def redirect(self, ctx):
        if self.Cachable:
            ctx.add_cache_control("private")
        raise self.method(self.Target)

    def resolve_path(self, ctx, relpath):
        if relpath != "":
            raise Errors.NotFound(resource=fullpath)
        if self.method is Errors.InternalRedirect:
            raise self.method(self.Target)
        else:
            return self

    @property
    def Cachable(self):
        return self.cachable

    request_handlers = redirect

class RedirectInternal(RedirectBase):
    __metaclass__ = Registry.NodeMeta

    namespace = RedirectBase.namespace
    names = ["internal"]

    class Info(Navigation.Info):
        def __init__(self, ctx, redirect):
            self.redirect = redirect
            self.super_info = redirect.TargetNode.get_navigation_info(ctx)
            self.display = redirect._navdisplay
            self.title = redirect._navtitle or self.super_info.get_title()

        def get_title(self):
            return self.title

        def get_display(self):
            return self.display

        def get_representative(self):
            return self.redirect


    def __init__(self, site, parent, node):
        super(RedirectInternal, self).__init__(site, parent, node)
        self.to = node.get("to")
        self._navtitle = node.get("nav-title")
        self._navdisplay = Navigation.DisplayMode(node.get("nav-display", Navigation.Show))

    @property
    def TargetNode(self):
        if hasattr(self, "target_node"):
            return self.target_node
        else:
            self.target_node = self.site.get_node(self.to)
            return self.target_node

    @property
    def Target(self):
        return self.TargetNode.Path.encode("utf-8")

    def get_navigation_info(self, ctx):
        return self.Info(ctx, self)
