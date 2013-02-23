# File name: Feeds.py
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
from __future__ import unicode_literals, print_function, absolute_import

import logging

from PyXWF.utils import ET, _F
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Types as Types

import PyWeblog.Node as Node
import PyWeblog.Protocols as Protocols

logger = logging.getLogger(__name__)

class Feeds(Node.Tweak, Protocols.Feeds):
    __metaclass__ = Registry.NodeMeta

    namespace = unicode(NS.PyBlog)
    names = ["feeds"]

    def __init__(self, site, parent, node):
        super(Feeds, self).__init__(site, parent, node)
        self._protocols = []
        self._protocolmap = {}
        self._queryparam = Types.NotEmpty(node.get("query-param", "feed"))

        for child in node:
            if child.tag == ET.Comment:
                continue
            protocol = Registry.NodePlugins.get(child, site, self)
            if not isinstance(protocol, Protocols.Feed):
                raise Errors.BadChild(protocol, self)
            self.register_protocol(protocol)

        self.Blog.Feeds = self

    def get_feeds_node(self, for_directory):
        feeds = NS.PyBlog("feeds")
        feeds.set("query-param", self._queryparam)
        for protocol in self._protocols:
            feeds.append(protocol.get_feed_node())
        return feeds

    def register_protocol(self, protocol):
        value = protocol.QueryValue
        if value in self._protocolmap:
            raise Errors.NodeConfigurationError("Conflict: duplicate parameter value: {0}".format(value))
        self._protocols.append(protocol)
        self._protocolmap[value] = protocol
        logger.debug(_F("Registered {0} as query value {1}", protocol, value))

    def resolve_feed_node(self, node, ctx, super_resolve, relpath):
        """
        .. see-also::
            :meth:`PyWeblog.Protocols.Feeds.resolve_feed_node` documentation
            before reading this.

        The algorithm to determine the result should be the following:

        1.  Check if relpath is the empty string.

            *   **If not**: Return the result of ``super_resolve(ctx, relpath)``
                and abort.

        1.  Check if the query parameter used to detect a feed request is
            present in *ctx*.

            *   **If not**: Return the result of ``super_resolve(ctx, relpath)``
                and abort.

        2.  Check if the value of the query parameter matches a feed protocol
            supported.

            * **If not**: Return :data:`None` and abort.

        3.  Return the appropriate node implementing the feed protocol.
        """
        if relpath:
            return super_resolve(ctx, relpath)
        try:
            value = ctx.QueryData[self._queryparam].pop()
        except IndexError:
            value = None
        except KeyError:
            return super_resolve(ctx, relpath)

        try:
            feednode = self._protocolmap[value]
        except KeyError:
            return None

        return feednode.proxy(ctx, node)

    request_handlers = {}
