# File name: TagCloud.py
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

    def render(self, ctx, parent):
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
        yield ul
