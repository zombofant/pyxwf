# File name: __init__.py
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
import abc

class CrumbBase(object):
    """
    Usually, you'll inherit from this baseclass to implement a Crumb. It takes
    two arguments. *site* must be the :class:`~PyXWF.Site.Site` instance to
    which the crumb belongs and *node* must be the :class:`lxml.etree._Element`
    instance which triggered instanciaton of the crumb.

    Note that to create a crumb, you have to use the
    :class:`~PyXWF.Registry.CrumbMeta` metaclass, which requires some
    attributes::

        class SomeFancyCrumb(CrumbBase):
            __metaclass__ = Registry.CrumbMeta

            # xml namespace
            namespace = "http://example.com/some-fancy-crumb"

            # list of xml local-names to register for in the above namespace
            names = ["crumb"]
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, site, node):
        super(CrumbBase, self).__init__()
        self.site = site
        self.ID = node.get("id")

    @abc.abstractmethod
    def render(self, ctx, parent):
        """
        Return an iterable of nodes which are to be inserted into the node
        *parent*. As indicated by the lack of hint on where to insert, an
        implementor of this method *should not* insert the nodes by itself.

        It is perfectly fine (and even recommended) to implement this as a
        generator function.
        """
