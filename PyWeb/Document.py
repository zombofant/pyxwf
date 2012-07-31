import abc

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

    @abc.abstractmethod
    def parse(self, filelike):
        """
        Take a *filelike* and parse the hell out of it. Return a :cls:`Document`
        instance with all data filled out.
        
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
    """
    
    def __init__(self, title, keywords, links, body):
        super(Document, self).__init__()
        self.title = title
        self.keywords = keywords
        self.links = links
        self.body = body
