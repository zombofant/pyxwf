from __future__ import unicode_literals, absolute_import, print_function

import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Types as Types

import PyWeblog.GenericFeed as GenericFeed

class Atom(GenericFeed.GenericFeed):
    __metaclass__ = Registry.NodeMeta

    namespace = str(NS.PyBlog)
    names = ["atom-feed"]

    ContentType = ContentTypes.Atom

    def __init__(self, site, parent, node):
        super(Atom, self).__init__(site, parent, node)
        self._query_value = Types.NotEmpty(node.get("query-value", "atom"))
        self._template = Types.NotEmpty(Types.NotNone(node.get("template")))
        self._favicon = node.get("favicon")

    def transform(self, ctx, root):
        root.set("icon", self._favicon or "")
        self._favicon = self.site.transform_href(ctx, root, attrname="icon", make_global=True)
        feed = super(Atom, self).transform(ctx, root)
        transform_href = self.site.transform_href
        for locallink in feed.iter(NS.PyWebXML.link):
            locallink.tag = NS.Atom.link
            transform_href(ctx, locallink)
            locallink.text = self._link_prefix[:-1]+locallink.get("href")
            del locallink.attrib["href"]
        return feed

    # these are handled by a proxy class. this instance is _never_ returned as
    # handling node
    request_handlers = {}
