from __future__ import unicode_literals, print_function, absolute_import

import logging

from PyXWF.utils import ET, _F
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Types as Types

import PyWeblog.Node as Node
import PyWeblog.Protocols as Protocols

class Feeds(Node.Tweak, Protocols.Feeds):
    __metaclass__ = Registry.NodeMeta

    namespace = unicode(NS.PyBlog)
    names = ["feeds"]

    def __init__(self, site, parent, node):
        super(Feeds, self).__init__(site, parent, node)
        self._protocols = []
        self._protocolMap = {}
        self._queryParam = Types.NotEmpty(node.get("query-param", "feed"))

        for child in node:
            if child.tag == ET.Comment:
                continue
            protocol = Registry.NodePlugins.getPluginInstance(child, site, self)
            if not isinstance(protocol, Protocols.Feed):
                raise Errors.BadChild(protocol, self)
            self.registerProtocol(protocol)

        self.Blog.Feeds = self

    def getFeedsNode(self, forDirectory):
        feeds = NS.PyBlog("feeds")
        feeds.set("query-param", self._queryParam)
        for protocol in self._protocols:
            feeds.append(protocol.getFeedNode())
        return feeds

    def registerProtocol(self, protocol):
        value = protocol.QueryValue
        if value in self._protocolMap:
            raise Errors.NodeConfigurationError("Conflict: duplicate parameter value: {0}".format(value))
        self._protocols.append(protocol)
        self._protocolMap[value] = protocol
        logging.debug(_F("Registered {0} as query value {1}", protocol, value))

    def resolveFeedNode(self, node, ctx, superResolve, relPath):
        """
        .. see-also::
            :meth:`PyWeblog.Protocols.Feeds.resolveFeedNode` documentation
            before reading this.

        The algorithm to determine the result should be the following:

        1.  Check if relPath is the empty string.

            *   **If not**: Return the result of ``superResolve(ctx, relPath)``
                and abort.

        1.  Check if the query parameter used to detect a feed request is
            present in *ctx*.

            *   **If not**: Return the result of ``superResolve(ctx, relPath)``
                and abort.

        2.  Check if the value of the query parameter matches a feed protocol
            supported.

            * **If not**: Return :data:`None` and abort.

        3.  Return the appropriate node implementing the feed protocol.
        """
        if relPath:
            return superResolve(ctx, relPath)
        try:
            value = ctx.QueryData[self._queryParam].pop()
        except IndexError:
            value = None
        except KeyError:
            return superResolve(ctx, relPath)

        try:
            feedNode = self._protocolMap[value]
        except KeyError:
            return None

        return feedNode.proxy(ctx, node)

    requestHandlers = {}
