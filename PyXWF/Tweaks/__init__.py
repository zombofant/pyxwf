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
from __future__ import unicode_literals

import itertools

from PyXWF.utils import ET
import PyXWF.Namespaces as NS
import PyXWF.Sitleton as Sitleton

def TweakContainer():
    return ET.Element(NS.Site.tweaks)

class TweakSitleton(Sitleton.Sitleton):
    """
    Baseclass for a Sitleton which hooks into tweak nodes from the sitemap. Do
    not instanciate this directly, it's of not much use for you.

    *tweak_ns* must be the xml namespace URI of the namespace for which you want
    to register nodes. Then you have two options of registering hooks for nodes,
    which can be combined:

    1.  *tweak_names* takes a list of strings and is by default the empty list.
        Each string you pass will be combined with *tweak_ns* and passed to the
        :class:`~PyXWF.Registry.TweakRegistry` instance of the site together
        with the method :meth:`tweak` _you_ have to declare and implement.

        It is not declared as abstractmethod in this class as this won't be
        neccessary for successful use if you use the second method below.

    2.  *tweak_hooks* must be a list of tuples, with the first element being the
        local-name of the node you want to register a hook for. This is again
        combined with the *tweak_ns* to form a fully qualified XML node name.
        The second element must be a callable which will be called whenever the
        :class:`~PyXWF.Site` instance hits a node with the respective tag.

    Both :meth:`tweak` and the callables you pass in *tweak_hooks* must take
    exactly one positional argument, which will be the node which was
    encountered. You may do all nasty things with that node, it's discarded
    afterwards.

    Example::

        import PyXWF.Registry as Registry
        import PyXWF.Tweaks as Tweaks

        class MyFancySitleton(Tweaks.TweakSitleton):
            __metaclass__ = Registry.SitletonMeta  # do not forget this!

            namespace = "http://example.com/my-fancy-sitleton"

            def __init__(self, site):
                super(MyFancySitleton, site).__init__(site,
                    tweak_ns=self.namespace,
                    tweak_names=["nodeA", "nodeC"]
                    tweak_hooks=[
                        ("nodeB", self.nodeB)
                    ]
                )

            def tweak(self, node):
                # this will be called for each nodeA and nodeC in the namespace
                # encountered in the <site:tweaks /> node of the site.
                pass

            def nodeB(self, node):
                # this will be called for each nodeB in our namespace
                # encountered in the <site:tweaks /> node of the site.
                pass

    """

    def __init__(self, site,
            tweak_ns=None,
            tweak_names=[],
            tweak_hooks=[],
            **kwargs):
        super(TweakSitleton, self).__init__(site, **kwargs)
        if tweak_names:
            site.tweak_registry.register(self,
                # this creates the neccessary keys for the registry
                itertools.izip(itertools.repeat(tweak_ns),
                    itertools.izip(tweak_names, itertools.repeat(self.tweak))
                )
            )
        if tweak_hooks:
            site.tweak_registry.register(self,
                itertools.izip(itertools.repeat(tweak_ns), tweak_hooks)
            )

