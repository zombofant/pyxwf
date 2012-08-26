from __future__ import unicode_literals

import itertools, abc

from PyXWF.utils import ET
import PyXWF.Namespaces as NS
import PyXWF.Sitleton as Sitleton

def TweakContainer():
    return ET.Element(NS.Site.tweaks)

class TweakSitleton(Sitleton.Sitleton):
    __metaclass__ = abc.ABCMeta

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

