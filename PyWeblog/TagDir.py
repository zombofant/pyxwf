# File name: TagDir.py
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

import abc
import operator
import copy
import os
import logging

from PyXWF.utils import ET, _F
import PyXWF.Nodes as Nodes
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.Navigation as Navigation

import PyWeblog.Node as BlogNode
import PyWeblog.Protocols as Protocols

logger = logging.getLogger(__name__)

class TagDir(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info,
        Protocols.TagDir):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["tag-dir"]

    def __init__(self, site, parent, node):
        if not isinstance(parent, BlogNode.Blog):
            raise Errors.BadParent(self, parent)
        super(TagDir, self).__init__(site, parent, node)
        self.Blog = parent
        self.index = self.Blog.index

        self._children = {}
        self._child_list = []

        self._navtitle = Types.NotNone(node.get("nav-title"))
        self._navdisplay = Navigation.DisplayMode(node.get("nav-display", "show"))
        self._show_pages_in_nav = Types.Typecasts.bool(node.get("show-pages-in-nav", False))
        self._page_title_fmt = node.get("page-nav-title-format", "{tag} tag")
        self._list_template = Types.NotNone(node.get("list-template"))

        self._fixed_children = {}
        for child in node:
            if child.tag == ET.Comment:
                continue
            if not child.get("name"):
                self._template_node = child
                continue
            node = Registry.NodePlugins.get(child, site, self)
            if not isinstance(node, TagPage):
                raise Errors.BadChild(node, self)
            self._fixed_children[node.Name] = node
        try:
            self._template_node
        except AttributeError:
            raise Errors.NodeConfigurationError("Tag dir requires template node (<blog:tag-page /> without name)", self)

        self.Blog.TagDirectory = self

    def _get_child(self, key):
        if key == "":
            return self
        else:
            return self._children.get(key, None)

    def do_GET(self, ctx):
        tag_list = NS.PyBlog("tag-list")
        for posts, page in reversed(self._child_list):
            tag = page.Name
            tagel = ET.SubElement(tag_list, NS.PyBlog.tag, attrib={
                "href": self.get_tag_page_path(tag),
                "post-count": unicode(posts)
            })
            tagel.text = tag
        return self.site.template_cache[self._list_template].transform(tag_list)

    def get_tag_page_path(self, tag):
        return self.Path + tag

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self._navtitle

    def get_display(self):
        return self._navdisplay

    def get_representative(self):
        return self

    def resolve_path(self, ctx, relpath):
        node = super(TagDir, self).resolve_path(ctx, relpath)
        if node is self:
            ctx.use_resource(self.site.template_cache[self._list_template])
        return node

    def update_children(self):
        self._children = {}
        self._child_list = []
        for keyword, posts in self.index.get_keyword_posts():
            try:
                page = self._fixed_children[keyword]
            except KeyError:
                self._template_node.set("name", keyword)
                page = TagPage(self.site, self, self._template_node)
            self._children[keyword] = page
            self._child_list.append((len(posts), page))
            page.update_children(posts)
        self._child_list.sort(key=lambda x: (x[0], x[1].Name))
        logger.debug(_F("Tag dir updated: {0} children", len(self._child_list)))
        logger.debug(_F("Tags: {0}", ", ".join(self._children.keys())))

    def __iter__(self):
        if self._show_pages_in_nav:
            return iter(page for count, page in self._child_list)
        else:
            return iter([])

    def __len__(self):
        return len(self._child_list)

    request_handlers = {
        "GET": do_GET
    }

class TagPage(Protocols.FeedableDirectoryMixin, Nodes.Node, Navigation.Info, Protocols.PostDirectory):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["tag-page"]

    SelectionCriterion = "tag"

    def __init__(self, site, parent, node):
        if not isinstance(parent, TagDir):
            raise Errors.BadParent(self, parent)
        super(TagPage, self).__init__(site, parent, node)
        self.Blog = parent.Blog
        self._posts = []
        self._title = (node.get("nav-title-fmt") or parent._page_title_fmt).format(tag=self.Name)
        self._list_template = Types.NotNone(node.get("list-template"))
        self._feeds_node = None

    @property
    def SelectionValue(self):
        return self.Name

    def do_GET(self, ctx):
        if not self._feeds_node and self.Blog.Feeds:
            feeds = self.Blog.Feeds.get_feeds_node(self)
            feeds.set("base", self.Path)
            self.abstracts.append(feeds)
            self._feeds_node = feeds
        return self.site.template_cache[self._list_template].transform(
            self.abstracts,
            self.Blog.get_transform_args()
        )

    def resolve_path(self, ctx, relPath):
        result = super(TagPage, self).resolve_path(ctx, relPath)
        if result is self:
            ctx.use_resource(self.site.template_cache[self._list_template])
        return result

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self._title

    def get_display(self):
        return Navigation.Show

    def get_representative(self):
        return self

    def get_posts(self):
        return self._posts

    def update_children(self, posts):
        self._posts = list(reversed(posts))
        self.abstracts = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "tag": self.Name
        })
        for post in self._posts:
            self.abstracts.append(copy.deepcopy(post.abstract))

    request_handlers = {
        "GET": do_GET
    }

