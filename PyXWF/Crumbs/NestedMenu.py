# File name: NestedMenu.py
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
import logging

from PyXWF.utils import ET, _F
import PyXWF.utils as utils
import PyXWF.Types as Types
import PyXWF.Namespaces as NS
import PyXWF.Registry as Registry
import PyXWF.Crumbs as Crumbs
import PyXWF.Navigation as Nav

logger = logging.getLogger(__name__)

class IteratorStack(object):
    def __init__(self):
        self.stack = []
        self.curr = None

    def push(self, new):
        if self.curr is not None:
            self.stack.append(self.curr)
            self.curr = new
        else:
            self.curr = new

    def next(self):
        try:
            return next(self.curr)
        except StopIteration:
            try:
                self.curr = self.stack.pop()
                return next(self)
            except IndexError:
                raise StopIteration()

    def __iter__(self):
        return self

class Navigation(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta

    namespace = "http://pyxwf.zombofant.net/xmlns/crumbs/navigation"
    names = ["crumb"]

    def __init__(self, site, node):
        depth_range = Types.NumericRange(int, 0, None)
        super(Navigation, self).__init__(site, node)
        self.root = site.get_node(node.get("root"))
        self.show_root = Types.DefaultForNone(False, Types.Typecasts.bool)\
                                            (node.get("show-root"))
        self.maxdepth = Types.DefaultForNone(None, depth_range)\
                                            (node.get("max-depth"))
        self.mindepth = Types.DefaultForNone(None, depth_range)\
                                            (node.get("min-depth"))
        self.active_class = node.get("active-class", "nav-active")
        self.child_active_class = node.get("child-active-class")
        self.mindisplay = Types.Typecasts.int(node.get("min-display", 1))
        self.root_as_header = Types.DefaultForNone(False,
            Types.NumericRange(int, 1, 6))(node.get("root-as-header"))
        self.pass_id = Types.Typecasts.bool(node.get("pass-id", False));

    @staticmethod
    def page_representative(ctx, page):
        return page.get_navigation_info(ctx).get_representative()

    def _propagate_active(self, enode):
        if not self.child_active_class:
            return
        cls = self.child_active_class
        while enode is not None:
            if enode.tag == NS.XHTML.li:
                a = enode.find(NS.XHTML.a)
                if a is not None:
                    utils.add_class(a, cls)
            enode = enode.getparent()

    def _markupA(self, ctx, parent, node, nav_info, active_chain, deepest=False):
        a = ET.SubElement(parent, NS.PyWebXML.a, href=node.Path)
        a.text = nav_info.get_title()
        representative = nav_info.get_representative()
        if self.pass_id and node.ID:
            a.set("id", node.ID)
        if representative in active_chain:
            pagenode = self.page_representative(ctx, ctx.PageNode)
            if deepest or representative is pagenode:
                if self.active_class:
                    utils.add_class(a, self.active_class)
            else:
                if self.child_active_class:
                    utils.add_class(a, self.child_active_class)
        return a

    def _nav_tree(self, parent, ctx, info, depth=0, active_chain=set(), active=False):
        if self.maxdepth is not None and depth > self.maxdepth:
            return
        if not (active or self.mindepth is None or depth <= self.mindepth):
            return
        nodeiter = IteratorStack()
        try:
            nodeiter.push(iter(info))
        except (ValueError, TypeError):
            return
        if parent is not None:
            ul = ET.SubElement(parent, NS.XHTML.ul)
        else:
            ul = ET.Element(NS.XHTML.ul)

        for child in nodeiter:
            nav_info = child.get_navigation_info(ctx)
            display_mode = nav_info.get_display()
            if display_mode is Nav.ReplaceWithChildren:
                nodeiter.push(iter(nav_info))
            elif display_mode >= self.mindisplay:
                li = ET.SubElement(ul, NS.XHTML.li)
                a = self._markupA(ctx, li, child, nav_info, active_chain, depth==self.maxdepth)
                subtree = self._nav_tree(li, ctx, nav_info, depth+1, active_chain,
                    active=self.page_representative(ctx, child) in active_chain)
                if subtree is not None:
                    li.append(subtree)
        return ul

    def render(self, ctx, parent):
        if ctx.PageNode:
            active_chain = frozenset(map(
                lambda x: self.page_representative(ctx, x),
                ctx.PageNode.iter_upwards()
            ))
        else:
            active_chain = frozenset()
        logging.debug(_F("active chain: {}", active_chain))
        if self.show_root:
            if self.root_as_header is not None:
                logger.debug("root w/ root as header")
                tree = self._nav_tree(None, ctx, self.root.get_navigation_info(ctx),
                    depth=1,
                    active_chain=active_chain,
                    active=self.root in active_chain)
                header = ET.Element(NS.XHTML.header)
                hX = ET.SubElement(header,
                    getattr(NS.XHTML, "h{0}".format(self.root_as_header)))
                self._markupA(ctx, hX, self.root,
                    self.root.get_navigation_info(ctx),
                    active_chain=active_chain)
                yield header
                if tree is not None:
                    yield tree
            else:
                logger.debug("root w/o root as header")
                tree = self._nav_tree(None, ctx, [self.root],
                    depth=0,
                    active_chain=active_chain,
                    active=True)
                if tree is not None:
                    yield tree
        else:
            logger.debug("no root")
            tree = self._nav_tree(None, ctx, self.root.get_navigation_info(ctx),
                active_chain=active_chain,
                active=True)
            if tree is not None:
                yield tree
