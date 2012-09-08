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
        self.section_links = False
        self.anchor_prefix = Types.NotEmpty(node.get("anchor-prefix", "sec-"))
        self.show_root = Types.Typecasts.bool(
            node.get("show-root", False)
        )
        self.tag_only = Types.Typecasts.bool(
            node.get("tag-only", False)
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
        for child in header_node:
            if child.tag in self.header_tags:
                hX = child
                break
        else:
            return None

        idx = header_node.index(hX)
        print(ET.tostring(hX))
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

    def render(self, ctx, parent):
        ul = ET.Element(NS.XHTML.ul)
        _, name = utils.split_tag(parent.tag)
        if name != "section" and name != "article":
            parent = parent.getparent()
        section_stack = []
        self._subtree(ctx, ul, parent, section_stack)
        if not self.tag_only:
            yield ul



