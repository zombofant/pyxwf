# File name: Protocols.py
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
from __future__ import absolute_import, unicode_literals, print_function

import abc

class PostDirectory(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_posts(self):
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
    def get_tag_page_path(self, tag):
        """
        Return the node path of the TagPage belonging to *tag*.
        """

class Feeds(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_feeds_node(self, for_directory):
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
    def resolve_feed_node(self, node, ctx, super_resolve, relpath):
        """
        Return either the normal result of *super_resolve* or this object,
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
    def get_feed_node(self):
        """
        Return the ``<blog:feed />`` node as described in
        :meth:`Feeds.get_feeds_node`.
        """

class FeedableDirectoryMixin(object):
    def resolve_path(self, ctx, relpath):
        super_resolve = super(FeedableDirectoryMixin, self).resolve_path
        if self.Blog.Feeds:
            return self.Blog.Feeds.resolve_feed_node(self, ctx, super_resolve, relpath)
        else:
            return super_resolve(ctx, relpath)
