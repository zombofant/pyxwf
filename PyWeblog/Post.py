from __future__ import unicode_literals

import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation
import PyXWF.Namespaces as NS

class PostNode(Nodes.Node, Navigation.Info):
    def __init__(self, parent, post):
        super(PostNode, self).__init__(parent.site, parent, None)
        self.Blog = parent.Blog
        self._path = parent.Path + post.basename
        self._name = post.basename
        self.post = post

    def resolve_path(self, ctx, relpath):
        node = super(PostNode, self).resolve_path(ctx, relpath)
        if node is self:
            ctx.use_resource(self.post)
        return node

    def do_GET(self, ctx):
        return self.site.template_cache[self.Blog.post_template].transform(
            self.post.get_PyWebXML(),
            self.Blog.get_transform_args()
        )

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self.post.title

    def get_display(self):
        return Navigation.Show

    def get_representative(self):
        return self

    request_handlers = {
        "GET": do_GET
    }
