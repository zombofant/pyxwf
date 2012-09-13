from __future__ import unicode_literals, print_function, absolute_import

import copy

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Registry as Registry
import PyXWF.Crumbs as Crumbs
import PyXWF.Types as Types
import PyXWF.Errors as Errors

class Breadcrumbs(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    namespace = "http://pyxwf.zombofant.net/xmlns/crumbs/toc"
    names = ["crumb"]

    header_tags = set(getattr(NS.XHTML, "h{0}".format(i)) for i in range(1, 7))

    def __init__(self, site, node):
        super(Breadcrumbs, self).__init__(site, node)
        self.section_numbers = Types.Typecasts.bool(
            node.get("section-numbers", True)
        )
        self.section_number_class = node.get("section-number-class", "toc-section-number")
        self.header_class = node.get("header-class", "toc-header")
        self.section_links = False
        self.anchor_prefix = Types.NotEmpty(node.get("anchor-prefix", "sec-"))
        self.target = node.get("target")
        self.show_root = Types.Typecasts.bool(
            node.get("show-root", False)
        )
        self.tag_only = Types.Typecasts.bool(
            node.get("tag-only", False)
        )
        self.legacy_topology = Types.Typecasts.bool(
            node.get("legacy-topology", False)
        )
        self.maxdepth = Types.DefaultForNone(None, Types.NumericRange(int, 1, None))(node.get("max-depth"))
        for child in node:
            if child.tag is ET.Comment:
                pass
            if child.tag == NS.XHTML.a:
                if child.get("id") == "seclink":
                    self.section_links = True
                    self.section_link_template = copy.deepcopy(child)
                    continue
            raise Errors.BadChild(child, node)


    def _header(self, ctx, header_node, list_parent, section_stack):
        if header_node.tag in self.header_tags:
            hX = header_node
        else:
            for child in header_node:
                if child.tag in self.header_tags:
                    hX = child
                    break
            else:
                return None

        if self.header_class is not None:
            utils.add_class(header_node, self.header_class)
        id = hX.get("id")
        section_number = ".".join(map(unicode, section_stack))
        if id is None:
            id = self.anchor_prefix + section_number
            hX.set("id", id)
        section_title = "".join(hX.itertext())
        if self.section_numbers:
            if hX.text:
                text = hX.text
                hX.text = ""
                ET.SubElement(hX, NS.XHTML.span).text = text
            secno_node = ET.Element(NS.XHTML.span, attrib={
                "class": self.section_number_class
            })
            secno_node.text = section_number
            hX.insert(0, secno_node)
        if self.section_links:
            if hX.text:
                text = hX.text
                hX.text = ""
                ET.SubElement(hX, NS.XHTML.span).text = text
            seclink_node = copy.deepcopy(self.section_link_template)
            seclink_node.set("href", "#" + id)
            hX.append(seclink_node)

        li = ET.SubElement(list_parent, NS.XHTML.li)
        a = ET.SubElement(li, NS.XHTML.a, attrib={
            "href": "#"+id
        })
        if self.section_numbers:
            secno_node = ET.SubElement(a, NS.XHTML.span, attrib={
                "class": self.section_number_class
            })
            secno_node.text = section_number
        ET.SubElement(a, NS.XHTML.span).text = section_title

        return li

    def _subtree(self, ctx, list_parent, content_parent, section_stack, depth=0):
        if self.maxdepth is not None and depth > self.maxdepth:
            return
        if depth > 0 or self.show_root:
            if depth == 0:
                section_stack.append(1)
            for header in content_parent.iterchildren(tag=NS.XHTML.header):
                li = self._header(ctx, header, list_parent, section_stack)
                if li is not None:
                    list_parent = ET.SubElement(li, NS.XHTML.ul)
                    break

        for i, section in enumerate(content_parent.iterchildren(tag=NS.XHTML.section)):
            section_stack.append(i+1)
            self._subtree(ctx, list_parent, section, section_stack, depth+1)
            section_stack.pop()

    def _next_hX(self, node):
        for sibling in node.itersiblings():
            if sibling.tag in self.header_tags:
                return sibling
        return None

    def _next_header(self, prev_hX):
        next_hX = self._next_hX(prev_hX)
        if next_hX is None:
            return (None, None)
        depth = int(next_hX.tag[-1])
        return next_hX, depth

    def _legacy_subtree(self, ctx, list_parent, hX, section_stack, depth=0):
        header_depth = int(hX.tag[-1])
        if depth > 0 or self.show_root:
            li = self._header(ctx, hX, list_parent, section_stack)

        i = 0
        next_hX, depth = self._next_header(hX)
        while next_hX is not None:
            if depth <= header_depth:
                return next_hX, depth

            ul = ET.SubElement(li, NS.XHTML.ul)
            i += 1
            section_stack.append(i)
            next_hX, depth = self._legacy_subtree(ctx, ul, next_hX, section_stack, depth+1)
            section_stack.pop()
        return None, None


    def _legacy_tree(self, ctx, list_parent, content_parent, section_stack):
        hX = content_parent[0]
        if hX.tag not in self.header_tags:
            hX = self._next_hX(hX)

        i = 0
        while hX is not None:
            i += 1
            section_stack.append(i)
            hX, _ = self._legacy_subtree(ctx, list_parent, hX, section_stack)
            section_stack.pop()

    def render(self, ctx, parent):
        ul = ET.Element(NS.XHTML.ul)
        section_stack = []
        if self.target is not None:
            root = parent.getroottree()
            parent = root.xpath("//*[@id={0}]".format(
                utils.unicode2xpathstr(self.target)
            ))
            if not parent:
                return
            parent = parent[0]
        else:
            _, name = utils.split_tag(parent.tag)
            if name != "section" and name != "article":
                parent = parent.getparent()
        if self.legacy_topology:
            self._legacy_tree(ctx, ul, parent, section_stack)
        else:
            self._subtree(ctx, ul, parent, section_stack)
        if not self.tag_only:
            yield ul



