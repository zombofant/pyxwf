from __future__ import unicode_literals

import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation
import PyXWF.Namespaces as NS

class PostNode(Nodes.Node, Navigation.Info):
    def __init__(self, parent, post):
        super(PostNode, self).__init__(parent.Site, parent, None)
        self.Blog = parent.Blog
        self._path = parent.Path + post.basename
        self._name = post.basename
        self.post = post

    def resolvePath(self, ctx, relPath):
        node = super(PostNode, self).resolvePath(ctx, relPath)
        if node is self:
            ctx.useResource(self.post)
        return node

    def doGet(self, ctx):
        return self.Site.templateCache[self.Blog.postTemplate].transform(
            self.post.getPyWebXML(),
            self.Blog.getTransformArgs()
        )

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self.post.title

    def getDisplay(self):
        return Navigation.Show

    def getRepresentative(self):
        return self

    requestHandlers = {
        "GET": doGet
    }
