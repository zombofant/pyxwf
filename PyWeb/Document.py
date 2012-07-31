import abc
import os
from datetime import datetime

class DocumentBase(object):
    """
    Baseclass for Document type implementations. Derived classes should use
    :cls:`PyWeb.Registry.DocumentMeta` as metaclass to automatically register
    with the doctype registry. See there for further documentation.

    Documents have to implement the `parse` method.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        pass

    def _lastModified(self, fileref, floatTimes=False):
        """
        If *filelike* is a file name or a file like with associated fileno which
        points to an actual file, return the date of last modification
        stored in the filesystem, **None** otherwise.

        By default, the times are truncated to full seconds. If you need the
        floating point part of the times (if supported by the platform), pass
        ``True`` to *floatTimes*.
        """
        try:
            if isinstance(fileref, basestring):
                st = os.stat(fileref)
            else:
                fno = fileref.fileno()
                if fno >= 0:
                    st = os.fstat(fno)
                else:
                    return None
        except (OSError, AttributeError):
            return None
        if floatTimes:
            mtime = st.st_mtime
        else:
            mtime = int(st.st_mtime)
        return datetime.utcfromtimestamp(mtime)

    @abc.abstractmethod
    def parse(self, fileref):
        """
        Take a file name or filelike in *fileref* and parse the hell out of it.
        Return a :cls:`Document` instance with all data filled out.
        
        Derived classes must implement this.
        """


class Document(object):
    """
    Contains all relevant information about a Document. *body* must be a valid
    xhtml body (as :mod:`lxml.etree` nodes). *title* must be a string-like
    containing the title which is used on the page. *keywords* must be an
    iterable of strings and *links* must be an iterable of etree nodes
    which resemble nodes to put into the xhtml header. These are used for
    stylesheet and script associations, but can also contain different elements.

    *lastModified* is optionally a :cls:`datetime.datetime` object representing
    the last modification date of the document. Can be *None* if unknown or not
    well defined and to prevent caching.

    *etag* is a short string like specified in
    `RFC 2616, Section 14.19 <https://tools.ietf.org/html/rfc2616#section-14.19>`_.
    Can be *None* to prevent caching.
    """
    
    def __init__(self, title, keywords, links, body,
            lastModified=None,
            etag=None):
        super(Document, self).__init__()
        self.title = title
        self.keywords = keywords
        self.links = links
        self.body = body
        self.lastModified = lastModified
        self.etag = etag
