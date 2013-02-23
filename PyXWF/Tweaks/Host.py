# File name: Host.py
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
import re
import os
import logging
import functools

from PyXWF.utils import _F
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.Tweaks as Tweaks
import PyXWF.Context as Context

logging = logging.getLogger(__name__)

class HostNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/tweaks/host"

class Host(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(HostNS)

    _redirect_method_type = Types.EnumMap({
        "301": Errors.MovedPermanently,
        "permanent": Errors.MovedPermanently,
        "302": Errors.Found,
        "found": Errors.Found,
        "303": Errors.SeeOther,
        "see-other": Errors.SeeOther,
        "307": Errors.TemporaryRedirect,
        "temporary": Errors.TemporaryRedirect
    })

    def __init__(self, site):
        super(Host, self).__init__(
            site,
            tweak_ns=self.namespace,
            tweak_hooks=[
                ("mobileness", self.tweak_mobileness),
                ("redirect", self.tweak_static_redirect),
                ("mobile-redirect", self.tweak_mobile_redirect),
                ("force-mobile", self.tweak_force_mobile)
            ]
        )

        self._mobileness = {}

    def _do_redirect(self, ctx, to_host, method):
        path = "{2}://{0}{1}".format(
            to_host,
            ctx.FullURI,
            ctx.URLScheme
        )
        raise method(location=path, local=False)

    def _static_redirect(self, src, dst, kind, ctx):
        if ctx.HostName == src:
            self._do_redirect(ctx, dst, kind)

    def _mobile_redirect(self, mapping, use_cookie, kind, ctx):
        logging.debug(_F(
            "probing mobile redirect at {0} with IsMobileClient={1}",
            ctx.HostName,
            ctx.IsMobileClient
        ))
        try:
            target = mapping[ctx.HostName, ctx.IsMobileClient]
            assert self._mobileness[target] == ctx.IsMobileClient
        except KeyError:
            return
        if use_cookie:
            try:
                ctx.Cookies[use_cookie]
            except KeyError:
                ctx.set_cookie(Context.Cookie(
                    use_cookie,
                    "been-there",
                    domain=ctx.HostName,
                    path=self.site.urlroot
                ))
            else:
                logging.debug("aborting mobile redirect: cookie is set")
                return

        self._do_redirect(ctx, target, kind)

    def _force_mobile(self, ctx):
        try:
            ctx.IsMobileClient = self._mobileness[ctx.HostName]
        except KeyError:
            pass

    def tweak_mobileness(self, node):
        for child in node.iterchildren(tag=HostNS.name):
            mobile = Types.Typecasts.bool(child.get("mobile", ""))
            hostName = Types.NotEmpty(child.text)
            self._mobileness[hostName] = mobile

    def tweak_static_redirect(self, node):
        src = Types.NotEmpty(node.get("src", ""))
        dst = Types.NotEmpty(node.get("dest", ""))
        method = Types.DefaultForNone(Errors.Found, self._redirect_method_type)\
                                     (node.get("method"))
        self.site.hooks.register(
            "handle.pre-lookup",
            functools.partial(self._static_redirect, src, dst, method)
        )
        logging.info(_F("Setup static redirect from {0} to {1}", src, dst))

    def tweak_mobile_redirect(self, node):
        mapping = {}
        use_cookie = Types.DefaultForNone(False, Types.NotEmpty)\
                                         (node.get("cookie"))
        kind = Types.DefaultForNone(Errors.Found, self._redirect_method_type)\
                                   (node.get("method"))
        for child in node.iterchildren(tag=HostNS.pair):
            first = Types.NotEmpty(child.get("first", ""))
            second = Types.NotEmpty(child.get("second", ""))
            first_mobileness = self._mobileness[first]
            second_mobileness = self._mobileness[second]
            if second_mobileness == first_mobileness:
                logging.warning(_F(
                    "Dropping mobile redirect pair {0} <-> {1} as both have the same mobileness ({2}) to avoid infinite redirection loop.",
                    first,
                    second,
                    first_mobileness
                ))
                continue
            mapping[first, second_mobileness] = second
            mapping[second, first_mobileness] = first
            logging.debug(_F(
                "Set up mobile redirect pair {0} ({2}) <-> {1} ({3})",
                first,
                second,
                first_mobileness,
                second_mobileness
            ))
        logging.debug(_F(
            "Using cookie {0} and method {1} for the above hosts",
            use_cookie,
            kind.title
        ))
        self.site.hooks.register(
            "handle.pre-lookup",
            functools.partial(self._mobile_redirect, mapping, use_cookie, kind)
        )

    def tweak_force_mobile(self, node):
        self.site.hooks.register(
            "handle.pre-lookup",
            self._force_mobile
        )
