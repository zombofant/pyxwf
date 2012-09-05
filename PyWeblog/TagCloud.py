from __future__ import unicode_literals, print_function, division

import operator, itertools

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Registry as Registry
import PyXWF.Crumbs as Crumbs
import PyXWF.Types as Types

class TagCloud(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta
    namespace = "http://pyxwf.zombofant.net/xmlns/weblog"
    names = ["tagcloud"]

    _levels_type = Types.DefaultForNone(2,
        Types.NumericRange(Types.Typecasts.int, 4, None)
    )
    _maxtags_type = Types.DefaultForNone(23,
        Types.NumericRange(Types.Typecasts.int, 1, None)
    )
    _class_prefix_type = Types.DefaultForNone("tagcloud-level-",
        Types.Typecasts.unicode
    )

    def __init__(self, site, node):
        super(TagCloud, self).__init__(site, node)
        self.Blog = site.get_node(node.get("blog-id"))
        self.maxlevel = self._levels_type(node.get("level-count")) - 1
        self.maxtags = self._maxtags_type(node.get("max-tags"))
        self.class_prefix = self._class_prefix_type(node.get("css-class-prefix"))

    def render(self, ctx, into_node, at_index):
        ul = ET.Element(NS.XHTML.ul)
        index = self.Blog.index
        tag_dir = self.Blog.TagDirectory
        ctx.use_resource(index)
        tags = ((tag, len(posts)) for tag, posts in
                            index.get_keyword_posts())

        # sort by count and remove those with lower counts
        tags = sorted(tags, key=operator.itemgetter(1), reverse=True)
        tags = tags[:self.maxtags]
        if len(tags) > 0:
            maxcount = tags[0][1]

        # sort by name now
        tags.sort(key=lambda x: x[0].lower())
        maxlevel = self.maxlevel
        for tag, count in tags:
            level = int(round(maxlevel * count / maxcount))
            li = ET.SubElement(ul, NS.XHTML.li, attrib={
                "class": self.class_prefix + str(level)
            })
            a = ET.SubElement(li, NS.PyWebXML.a, attrib={
                "href": tag_dir.get_tag_page_path(tag)
            })
            a.text = tag
        into_node.insert(at_index, ul)
