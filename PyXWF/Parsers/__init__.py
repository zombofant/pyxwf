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
import abc, itertools

import PyXWF.Namespaces as NS
import PyXWF.Sitleton as Sitleton

class ParserBase(Sitleton.Sitleton):
    """
    Baseclass for Parser implementations. As parsers are sitletons, they have
    to use the same metaclass. You usually will additionally want to derive
    from :class:`~PyXWF.Tweaks.TweakSitleton` for support for site-wide
    configuration of your parser::

        # order of inheritance matters!
        class RestParser(Tweaks.TweakSitleton, ParserBase):
            __metaclass__ = Registry.SitletonMeta

            def __init__(self, site):
                super(RestParser, self).__init__(site,
                    # pass keyword arguments to TweakSitleton
                )

            def parse(self, fileref):
                # fancy parsing happens here
                return Document.Document()

    Check out the :class:`~PyXWF.Tweaks.TweakSitleton` documentation for an
    example of arguments and their effects.

    Parsers have to implement the :meth:`parse` method.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, site, parser_mimetypes=[], **kwargs):
        super(ParserBase, self).__init__(site, **kwargs)
        site.parser_registry.register(self, parser_mimetypes)

    @classmethod
    def transform_headers(cls, body, header_offset):
        """
        *header_offset* must be a non-negative integer. That amount of header
        levels will be added to any ``<h:hN />`` elements encountered in the
        *body* element tree. A *header_offset* of 1 will thus convert
        all ``<h:h1 />`` to ``<h:h2 />``, all ``<h:h2 />`` to ``<h:h2 />`` and
        so on.

        If the conversion would result in a ``<h:h7 />`` or above, the tag
        is converted into a ``<h:p />`` tag.

        .. note::
            This operation is in-place and returns :data:`None`.
        """
        headers = reversed(xrange(1,7))
        matches = (getattr(NS.XHTML, "h{0}".format(i)) for i in headers)
        iterator = itertools.chain(*itertools.imap(body.iter, matches))
        for hX in iterator:
            i = int(hX.tag[-1:])
            i += header_offset
            if i > 6:
                tag = "p"
            else:
                tag = "h"+str(i)
            hX.tag = getattr(NS.XHTML, tag)

    @abc.abstractmethod
    def parse(self, fileref, header_offset=1):
        """
        Take a file name or filelike in *fileref* and parse the hell out of it.
        Return a :class:`~PyXWF.Document.Document` instance with all relevant
        data filled in.
        """
