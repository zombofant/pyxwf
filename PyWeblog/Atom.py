# File name: Atom.py
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
        return feed

    # these are handled by a proxy class. this instance is _never_ returned as
    # handling node
    request_handlers = {}
