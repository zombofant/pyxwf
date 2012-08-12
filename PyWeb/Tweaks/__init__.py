from __future__ import unicode_literals

from PyWeb.utils import ET
import PyWeb.Namespaces as NS

def TweakContainer():
    return ET.Element(NS.Site.tweaks)
