# encoding=utf-8
# File name: ThemeSwitch.py
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
from __future__ import print_function, absolute_import, unicode_literals

import logging
import itertools
import copy
from datetime import datetime, timedelta

from PyXWF.utils import ET, _F
import PyXWF.Types as Types
import PyXWF.Registry as Registry
import PyXWF.Tweaks as Tweaks
import PyXWF.Crumbs as Crumbs
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS
import PyXWF.Context as Context

logger = logging.getLogger(__name__)

class ThemeNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/tweaks/theme-switch"


class Theme(object):
    def __init__(self, name, **kwargs):
        super(Theme, self).__init__(**kwargs)

        self._name = name
        self._css = []

    @classmethod
    def from_node(cls, node):
        obj = cls(node.get("name", None))
        obj.load_from_node(node)
        return obj

    def load_from_node(self, node):
        self._css.extend(map(copy.deepcopy, node.iter(NS.PyWebXML.link)))

    @property
    def Name(self):
        return self._name or ""

    def __iter__(self):
        return itertools.imap(copy.deepcopy, self._css)


class MetaTheme(object):
    def __init__(self, name, *themes, **kwargs):
        super(MetaTheme, self).__init__(**kwargs)
        self._name = name
        self._themes = list(themes)

    @property
    def Name(self):
        return self._name

    def __iter__(self):
        return itertools.chain(*self._themes)

class ThemeSwitch(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    namespace = str(ThemeNS)

    def __init__(self, site):
        super(ThemeSwitch, self).__init__(
            site,
            tweak_ns=self.namespace,
            tweak_hooks=[
                ("theme", self.theme_node),
                ("cookie", self.cookie_node)
            ]
        )

        self._cookiename = "theme"
        self._themes = {}
        self._meta_themes = {}
        self._default_theme = None
        self.site.hooks.register("handle.pre-lookup", self.select_theme)
        self.site.has_theme_support = True

    def theme_node(self, node):
        name = node.get("name", None)
        if not name:
            name = None

        if name in self._themes:
            raise Errors.ConfigurationError("Duplicate theme name: {}".format(name))

        theme = Theme.from_node(node)
        self._themes[name] = theme

        if Types.Typecasts.bool(node.get("default", False)):
            if self._default_theme is not None:
                raise Errors.ConfigurationError("Multiple default themes found")
            self._default_theme = theme.Name

        if name is None:
            name = "⟨base⟩"
        logger.info("Found and loaded theme: {}".format(name))

    def cookie_node(self, node):
        if not node.text:
            raise Errors.ConfigurationError("<theme:cookie /> must have non-empty text for a cookie name")
        self._cookiename = node.text

    def _get_meta_theme(self, theme_name):
        try:
            return self._meta_themes[theme_name]
        except KeyError:
            try:
                upper_theme = self._themes[theme_name]
            except KeyError:
                return None
            base_theme = self._themes.get(None, None)
            meta_theme = MetaTheme(theme_name, base_theme, upper_theme)
            self._meta_themes[theme_name] = meta_theme
            return meta_theme

    def _set_theme(self, ctx, theme):
        ctx.Theme = theme

    def select_theme(self, ctx):
        querydict = ctx.QueryData
        if "settheme" in querydict:
            try:
                theme_name = querydict["settheme"][0]
            except IndexError:
                # this will make the subsequent check fail
                theme_name = 0

            if theme_name in self._themes:
                ctx.set_cookie(Context.Cookie(
                    self._cookiename,
                    theme_name,
                    expires=datetime.utcnow()+timedelta(days=365),
                    path=self.site.urlroot
                ))
                del querydict["settheme"]
                raise Errors.Found(
                    location=ctx.get_reconstructed_uri(self.site.urlroot),
                    local=False
                )

        try:
            cookie = ctx.Cookies[self._cookiename]
        except KeyError:
            theme_name = self._default_theme
        else:
            theme_name = cookie.value

        meta_theme = self._get_meta_theme(theme_name) \
                     or self._get_meta_theme(self._default_theme) \
                     or self._themes.get(None, None)

        self._set_theme(ctx, meta_theme)

    def __contains__(self, theme_name):
        return theme_name in self._themes

class ThemeCrumb(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta

    namespace = str(ThemeNS)
    names = ["stylesheets"]

    def __init__(self, site, node):
        super(ThemeCrumb, self).__init__(site, node)

    def render(self, ctx, parent):
        if ctx.Theme is None:
            logger.warn("theme not found")
            return
        logger.info("using theme: {}".format(ctx.Theme.Name))
        for node in ctx.Theme:
            yield node

class ThemeSwitchCrumb(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta

    namespace = str(ThemeNS)
    names = ["switch"]

    def __init__(self, site, node):
        super(ThemeSwitchCrumb, self).__init__(site, node)
        self._theme_name = Types.NotNone(node.get("to-theme"))
        if not self._theme_name in ThemeSwitch.at_site(site):
            raise Errors.ConfigurationError("Theme `{}' is no known theme at <theme:switch />".format(self._theme_name))
        try:
            self._link_template = list(node.iter(NS.XHTML.a))[0]
        except IndexError:
            raise Errors.ConfigurationError("<theme:switch /> requires an <h:a /> child to use as a template")
        self._hide_if_set = Types.Typecasts.bool(node.get("hide-if-set", False))

    def render(self, ctx, parent):
        if self._hide_if_set and ctx.Theme is not None and ctx.Theme.Name == self._theme_name:
            return

        a = copy.deepcopy(self._link_template)
        a.set("href", ctx.get_reconstructed_uri(
            self.site.urlroot,
            update_query={
                "settheme": self._theme_name
            }
        ))
        yield a

