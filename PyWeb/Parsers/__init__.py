import abc

class ParserBase(object):
    """
    Baseclass for Parser implementations. Derived classes should use
    :cls:`PyWeb.Registry.ParserMeta` as metaclass to automatically register
    with the doctype registry. See there for further documentation.

    Parsers have to implement the `parse` method.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        pass

    @abc.abstractmethod
    def parse(self, fileref):
        """
        Take a file name or filelike in *fileref* and parse the hell out of it.
        Return a :cls:`Document` instance with all data filled out.
        
        Derived classes must implement this.
        """
