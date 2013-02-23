# File name: Sitleton.py
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

class Sitleton(object):
    """
    .. note::
        If you want to create a sitleton, you probably want to be able to
        configure it. For that purpose, :class:`~PyXWF.Tweaks.TweakSitleton`
        is the correct baseclass.

    This is a pretty dumb baseclass which does nothing more than storing the
    value of *site* as :attr:`site`.

    However, this is useful when doing multiple inheritance to bring the diamond
    shape together at the right point (namely at :class:`Sitleton`), which
    doesn't break calling super() on init.
    """

    def __init__(self, site, **kwargs):
        super(Sitleton, self).__init__(**kwargs)
        self.site = site

    @classmethod
    def at_site(cls, site):
        """
        Return the sitleton instance of the class at which this method is called
        which has been instanciated at the :class:`~PyXWF.Site.Site` *site*.

        Raises :class:`~PyXWF.Errors.SitletonNotAvailable` if the sitleton has
        not been instanciated with exactly the class this method was called on
        at the given *site*.
        """
        try:
            return site.sitletons[cls]
        except KeyError:
            raise Errors.SitletonNotAvailable(cls, site)
