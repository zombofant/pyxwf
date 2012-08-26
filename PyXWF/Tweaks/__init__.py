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

    *tweakNS* must be the xml namespace URI of the namespace for which you want
    to register nodes. Then you have two options of registering hooks for nodes,
    which can be combined:

    1.  *tweakNames* takes a list of strings and is by default the empty list.
        Each string you pass will be combined with *tweakNS* and passed to the
        :class:`PyXWF.Registry.TweakRegistry` instance of the site together
        with the method :meth:`tweak` _you_ have to declare and implement.

        It is not declared as abstractmethod in this class as this won't be
        neccessary for successful use if you use the second method below.

    2.  *tweakHooks* must be a list of tuples, with the first element being the
        local-name of the node you want to register a hook for. This is again
        combined with the *tweakNS* to form a fully qualified XML node name.
        The second element must be a callable which will be called whenever the
        :class:`PyXWF.Site` instance hits a node with the respective tag.

    Both :meth:`tweak` and the callables you pass in *tweakHooks* must take
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
                    tweakNS=self.namespace,
                    tweakNames=["nodeA", "nodeC"]
                    tweakHooks=[
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
            tweakNS=None,
            tweakNames=[],
            tweakHooks=[],
            **kwargs):
        super(TweakSitleton, self).__init__(site, **kwargs)
        if tweakNames:
            site.tweakRegistry.register(self,
                # this creates the neccessary keys for the registry
                itertools.izip(itertools.repeat(tweakNS),
                    itertools.izip(tweakNames, itertools.repeat(self.tweak))
                )
            )
        if tweakHooks:
            site.tweakRegistry.register(self,
                itertools.izip(itertools.repeat(tweakNS), tweakHooks)
            )

