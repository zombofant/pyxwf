# File name: Breadcrumbs.py
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

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Registry as Registry
import PyXWF.Crumbs as Crumbs
import PyXWF.Navigation as Navigation
import PyXWF.Types as Types

class Breadcrumbs(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    namespace = "http://pyxwf.zombofant.net/xmlns/crumbs/breadcrumbs"
    names = ["crumb"]

    def __init__(self, site, node):
        super(Breadcrumbs, self).__init__(site, node)
        rootid = node.get("root")
        if rootid is not None:
            self.root = site.get_node(rootid)
        else:
            self.root = None
        self.force_show_current = Types.Typecasts.bool(
            node.get("force-show-current", False))
        self.mindisplay = Types.Typecasts.int(node.get("min-display", 1))
        self.rich = self._richmap(node.get("rich"))
        self.rdfa_prefix = node.get("rdfa-prefix", "v:")

    def render(self, ctx, parent):
        if not ctx.PageNode:
            return
        ul = ET.Element(NS.XHTML.ul)
        had_nodes = set()
        pagenode = ctx.PageNode
        for node in pagenode.iter_upwards():
            if node is self.root:
                break
            nav_info = node.get_navigation_info(ctx)
            display = nav_info.get_display()
            if ((display is Navigation.ReplaceWithChildren
                    or display < self.mindisplay)
                and (node is not pagenode or not self.force_show_current)):
                continue

            representative = nav_info.get_representative()
            if representative in had_nodes:
                continue

            had_nodes.add(representative)
            li = ET.Element(NS.XHTML.li)
            relevant = li
            if node is not pagenode:
                a = ET.SubElement(li, NS.PyWebXML.a, href=representative.Path)
                a.text = nav_info.get_title()
                relevant = a
                tail = False
            else:
                li.text = nav_info.get_title()
                tail = True
            self.rich(self, ctx, relevant, is_tail=tail)
            ul.insert(0, li)
        yield ul

    def rdfa(self, ctx, relevant_node, is_tail=False):
        prefix = self.rdfa_prefix
        if not is_tail:
            relevant_node.set("typeof", "v:Breadcrumb")
        else:
            relevant_node.set("typeof", "v:Breadcrumb")

    def schema(self, ctx, relevant_node, is_tail=False):
        relevant_node.set("property", "breadcrumb")
        if is_tail:
            relevant_node.set(NS.PyWebXML.content, ctx.PageNode.Path)

    def norich(self, *args, **kwargs):
        pass

    _richmap = Types.EnumMap({
        "rdfa": rdfa,
        "schema.org": schema,
        None: norich
    })
