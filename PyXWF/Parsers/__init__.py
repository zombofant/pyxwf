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

    def __init__(self, site, parserMimeTypes=[], **kwargs):
        super(ParserBase, self).__init__(site, **kwargs)
        site.parserRegistry.register(self, parserMimeTypes)

    @classmethod
    def transformHeaders(cls, body, headerOffset):
        """
        *headerOffset* must be a non-negative integer. That amount of header
        levels will be added to any ``<h:hN />`` elements encountered in the
        *body* element tree. A *headerOffset* of 1 will thus convert
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
            i += headerOffset
            if i > 6:
                tag = "p"
            else:
                tag = "h"+str(i)
            hX.tag = getattr(NS.XHTML, tag)

    @abc.abstractmethod
    def parse(self, fileref, headerOffset=1):
        """
        Take a file name or filelike in *fileref* and parse the hell out of it.
        Return a :class:`~PyXWF.Document.Document` instance with all relevant
        data filled in.
        """
