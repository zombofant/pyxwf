# File name: Directory.py
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
import itertools

from PyXWF.utils import ET

import PyXWF.Errors as Errors

import PyXWF.Registry as Registry
import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation

class DirectoryBase(Nodes.DirectoryResolutionBehaviour, Nodes.Node):

    class Info(Navigation.Info):
        def __init__(self, ctx, directory):
            self.children = directory.children
            self.display = directory.display
            self.index = directory.index
            self.super_info = self.index.get_navigation_info(ctx)

        def get_title(self):
            return self.super_info.get_title()

        def get_display(self):
            return self.display

        def get_representative(self):
            return self.index

        def __iter__(self):
            try:
                superiter = iter(self.super_info)
            except (ValueError, TypeError):
                superiter = iter([])
            return iter(itertools.chain(
                iter(superiter),
                itertools.ifilter(lambda x: x is not self.index, self.children)
            ))

    def __init__(self, site, parent, node):
        super(DirectoryBase, self).__init__(site, parent, node)
        self.pathdict = {}
        self.children = []
        self.display = Navigation.DisplayMode(
            node.get("nav-display", Navigation.Show) if node is not None else Navigation.Show)

    def _load_children(self, from_node):
        site = self.site
        for child in from_node:
            if child.tag is ET.Comment:
                continue
            self.append(Registry.NodePlugins(child, site, self))
        try:
            self.index = self.pathdict[""]
        except KeyError:
            raise ValueError("Directory requires index node (i.e. child node with unset or empty name)")

    def _get_child(self, key):
        return self.pathdict.get(key, None)

    def append(self, plugin):
        if plugin.Name in self.pathdict:
            raise ValueError("Duplicate path name {0!r} in {1}".format(plugin.Name, self.Path))
        self.pathdict[plugin.Name] = plugin
        self.children.append(plugin)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def get_navigation_info(self, ctx):
        return self.Info(ctx, self)

class Directory(DirectoryBase):
    __metaclass__ = Registry.NodeMeta

    namespace = "http://pyxwf.zombofant.net/xmlns/nodes/directory"
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Directory, self).__init__(site, parent, node)
        self._load_children(node)

class RootDirectory(Directory):
    __metaclass__ = Registry.NodeMeta

    namespace = Directory.namespace
    names = ["tree"]

    def __init__(self, site, parent, node):
        super(RootDirectory, self).__init__(site, parent, node)

    @property
    def Path(self):
        return None
