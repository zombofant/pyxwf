# File name: Recent.py
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

