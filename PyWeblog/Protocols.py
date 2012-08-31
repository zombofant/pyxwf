from __future__ import absolute_import, unicode_literals, print_function

import abc

class PostDirectory(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getPosts(self):
        """
        Return an iterable containing the posts displayed in this directory.
        This is used for example by the :class:`Feeds` protocol.
        """

    @abc.abstractproperty
    def SelectionCriterion(self):
        """
        The criterion on which the selection is based. This is passed e.g. to
        feed templates as @kind parameter.
        """

    @abc.abstractproperty
    def SelectionValue(self):
        """
        The value for the selection criterion on which the selection is based.
        This is passed to feed templates as @title parameter and should contain
        a human-readable value.
        """

class TagDir(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getTagPagePath(self, tag):
        """
        Return the node path of the TagPage belonging to *tag*.
        """

class Feeds(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getFeedsNode(self, forDirectory):
        """
        Return a ``<blog:feeds />`` node with the following attributes:

        :@query-param: The query parameter which is used to detect a feed is requested (e.g. ``feed``)

        The ``<blog:feeds />`` node must also contain a ``<blog:feed />`` node
        for each supported feed protocol with the following attributes:

        :@query-value: The value of the ``@query-param`` which represents this feed
        :@name: A short human-readable name of the feed format
        :@img-href: Reference of an image to use to represent this feed
        :@type: The MIME type of the feed
        """

    @abc.abstractmethod
    def resolveFeedNode(self, node, ctx, superResolve, relPath):
        """
        Return either the normal result of *superResolve* or this object,
        depending on the query parameters of the request. See the respective
        implementation for details on how the result is determined.

        The *node* must implement the :class:`PostDirectory` protocol.
        """

class Feed(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def QueryValue(self):
        """
        Must contain the query parameter value which uniquely identifies this
        syndication feed provider. Ideally, this should be user-configurable
        via the sitemap.
        """

    @abc.abstractmethod
    def proxy(self, ctx, node):
        """
        Return a :class:`PyXWF.Nodes.Node` compatible object which implements
        the neccessary request handlers to create the syndication feed.
        """

    @abc.abstractmethod
    def getFeedNode(self):
        """
        Return the ``<blog:feed />`` node as described in
        :meth:`Feeds.getFeedsNode`.
        """

class FeedableDirectoryMixin(object):
    def resolvePath(self, ctx, relPath):
        superResolve = super(FeedableDirectoryMixin, self).resolvePath
        if self.Blog.Feeds:
            return self.Blog.Feeds.resolveFeedNode(self, ctx, superResolve, relPath)
        else:
            return superResolve(ctx, relPath)
