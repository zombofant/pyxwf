from __future__ import unicode_literals, print_function, absolute_import

import itertools, copy

from PyXWF.utils import ET
import PyXWF.Nodes as Nodes
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.Navigation as Navigation

import PyWeblog.Node as BlogNode
import PyWeblog.Protocols as Protocols

class RecentPosts(Protocols.FeedableDirectoryMixin, Nodes.Node, Navigation.Info):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["recent"]

    _post_count_type = Types.NumericRange(int, 1, None)

    SelectionCriterion = ""
    SelectionValue = ""

    def __init__(self, site, parent, node):
        if not isinstance(parent, BlogNode.Blog):
            raise Errors.BadParent(self, parent)
        super(RecentPosts, self).__init__(site, parent, node)
        self.Blog = parent

        self._navtitle = Types.NotNone(node.get("nav-title"))
        self._navdisplay = Navigation.DisplayMode(node.get("nav-display", "show"))
        self._list_template = Types.NotNone(node.get("list-template"))
        self._post_count = self._post_count_type(node.get("post-count"))

    def resolve_path(self, ctx, relpath):
        result = super(RecentPosts, self).resolve_path(ctx, relpath)
        if result is self:
            ctx.use_resource(self.Blog.index)
            ctx.use_resource(self.site.template_cache[self._list_template])
        return result

    def do_GET(self, ctx):
        abstracts = NS.PyBlog("abstract-list")
        if self.Blog.Feeds:
            feeds = self.Blog.Feeds.get_feeds_node(self)
            feeds.set("base", self.Path)
            abstracts.append(feeds)
        postiter = itertools.islice(
            reversed(self.Blog.index.get_all_posts()),
            0,
            self._post_count
        )
        for post in postiter:
            abstracts.append(copy.deepcopy(post.abstract))
        return self.site.template_cache[self._list_template].transform(
            abstracts,
            self.Blog.get_transform_args()
        )

    def get_posts(self):
        return reversed(self.Blog.index.get_all_posts())

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self._navtitle

    def get_display(self):
        return self._navdisplay

    def get_representative(self):
        return self

    request_handlers = {
        "GET": do_GET
    }

