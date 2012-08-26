import abc, itertools

import PyXWF.Namespaces as NS
import PyXWF.Sitleton as Sitleton

class ParserBase(Sitleton.Sitleton):
    """
    Baseclass for Parser implementations. Derived classes should use
    :class:`PyXWF.Registry.ParserMeta` as metaclass to automatically register
    with the doctype registry. See there for further documentation.

    Parsers have to implement the `parse` method.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, site, parserMimeTypes=[], **kwargs):
        super(ParserBase, self).__init__(site, **kwargs)
        site.parserRegistry.register(self, parserMimeTypes)

    @classmethod
    def transformHeaders(cls, body, headerOffset):
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
    def parse(self, fileref):
        """
        Take a file name or filelike in *fileref* and parse the hell out of it.
        Return a :class:`Document` instance with all data filled out.

        Derived classes must implement this.
        """
