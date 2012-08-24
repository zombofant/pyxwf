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

    _levelsType = Types.DefaultForNone(2,
        Types.NumericRange(Types.Typecasts.int, 4, None)
    )
    _maxTagsType = Types.DefaultForNone(23,
        Types.NumericRange(Types.Typecasts.int, 1, None)
    )
    _classPrefixType = Types.DefaultForNone("tagcloud-level-",
        Types.Typecasts.unicode
    )

    def __init__(self, site, node):
        super(TagCloud, self).__init__(site, node)
        self.blog = site.getNode(node.get("blog-id"))
        self.maxLevel = self._levelsType(node.get("level-count")) - 1
        self.maxTags = self._maxTagsType(node.get("max-tags"))
        self.classPrefix = self._classPrefixType(node.get("css-class-prefix"))

    def render(self, ctx, intoNode, atIndex):
        ul = ET.Element(NS.XHTML.ul)
        ctx.useResource(self.blog)
        tags = ((tag, len(posts)) for tag, posts in
                            self.blog.viewTagPosts())
        tags = itertools.ifilter(lambda x: x[1], tags)  # remove empty tags

        # sort by count and remove those with lower counts
        tags = sorted(tags, key=operator.itemgetter(1), reverse=True)
        tags = tags[:self.maxTags]
        if len(tags) > 0:
            maxCount = tags[0][1]

        # sort by name now
        tags.sort(key=lambda x: x[0].lower())
        maxLevel = self.maxLevel
        for tag, count in tags:
            level = int(round(maxLevel * count / maxCount))
            li = ET.SubElement(ul, NS.XHTML.li, attrib={
                "class": self.classPrefix + str(level)
            })
            a = ET.SubElement(li, NS.PyWebXML.a, attrib={
                "href": self.blog.getTagPath(tag)
            })
            a.text = tag
        intoNode.insert(atIndex, ul)
