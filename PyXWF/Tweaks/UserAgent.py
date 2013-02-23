# File name: UserAgent.py
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
import re, logging

import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types

class UserAgentNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/tweaks/user-agent"

class ForceMobile(object):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(UserAgentNS)
    tweak_names = ["force-mobile"]

    def __init__(self, site):
        super(ForceMobile, self).__init__()
        site.hooks.register("handle.pre-lookup", self.force_mobile)
        self.site = site
        self.force_mobile = Types.Typecasts.bool(self._tweaks["force-mobile"][-1].get("mobile"))

    def force_mobile(self, ctx):
        ctx.IsMobileClient = self.force_mobile
        logging.debug("enforced mobileness to {0}".format(self.force_mobile))
