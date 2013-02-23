# File name: Post.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
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
            ctx.use_resource(self.site.template_cache[self.Blog.post_template])
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
