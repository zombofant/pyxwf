"""
In PyWeb, we call all content we send over the wire a Message. Messages thus
contain information about their mime type, encoding and of course their payload.

They represent it internally however they like, but must be able to serialize
the payload to a properly encoded bytes object for conversion in a MessageInfo
instance.
"""

import abc, copy

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Namespaces as NS
import PyWeb.ContentTypes as ContentTypes

class Message(object):
    """
    Baseclass for any message. For proper function, messages must implement
    the :meth:`getEncodedBody` method.

    It handles sending the message in a given transaction context if all
    properties and methods are set up properly.

    *mimeType* is the MIME type according to RFC 2046.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, mimeType, statusCode=200, encoding=None):
        super(Message, self).__init__()
        self._mimeType = mimeType
        self._encoding = encoding
        self._lastModified = None
        self._statusCode = statusCode

    @property
    def MIMEType(self):
        """
        The internet media type (aka *content type*) of the :cls:`Message`.
        """
        return self._mimeType

    @property
    def Encoding(self):
        """
        Encoding (charset in the Content Type context) of the message.
        """
        return self._encoding

    @Encoding.setter
    def Encoding(self, value):
        self._encoding = value

    @abc.abstractmethod
    def getEncodedBody(self):
        """
        Return the bytes object resembling the contents encoded in the encoding
        set up in :prop:`Encoding`.

        Derived classes must implement this method.
        """

    @property
    def StatusCode(self):
        return self._statusCode


class XHTMLMessage(Message):
    """
    Represent an XHTML message. *docTree* must be a valid XHTML document tree
    as lxml.etree node. Conversion to bytes payload is handled by this class
    automatically.
    """

    def __init__(self, docTree, **kwargs):
        super(XHTMLMessage, self).__init__(ContentTypes.xhtml, **kwargs)
        self._docTree = docTree
        try:
            # this is only available with lxml backend
            ET.cleanup_namespaces(self._docTree)
        except AttributeError:
            pass

    @property
    def DocTree(self):
        return self._docTree

    @DocTree.setter
    def DocTree(self, value):
        self._docTree = value

    def getEncodedBody(self):
        encoding = self.Encoding or "utf-8"
        return ET.tostring(self.DocTree,
            encoding=encoding,
            xml_declaration="yes",
            doctype="<!DOCTYPE html>"
        )


class HTMLMessage(Message):
    """
    Represent an HTML message. *docTree* must be a valid HTML document tree
    (the same as the XHTML tree, but without namespaces) as lxml.etree node.
    Conversion to bytes payload is handled by this class automatically.

    You can specify the HTML version via *version*, which is currently
    restricted to `HTML5`.
    """

    @classmethod
    def fromXHTMLTree(cls, docTree, version="HTML5", **kwargs):
        """
        Return an :cls:`HTMLMessage` instance from the given XHTML *docTree*.
        This performs automatic conversion by removing the XHTML namespace from
        all elements. Raises :cls:`ValueError` if a non-xhtml namespace is
        encountered.
        """
        docTree = copy.copy(docTree)
        utils.XHTMLToHTML(docTree)
        try:
            # this is only available with lxml backend
            ET.cleanup_namespaces(docTree)
        except AttributeError:
            pass
        return cls(docTree, version=version, **kwargs)

    def __init__(self, docTree, version="HTML5", **kwargs):
        if version != "HTML5":
            raise ValueError("Invalid HTMLMessage version: {0}".format(version))
        super(HTMLMessage, self).__init__(ContentTypes.html, **kwargs)
        self._docTree = docTree

    @property
    def DocTree(self):
        return self._docTree

    @DocTree.setter
    def DocTree(self, value):
        self._docTree = value

    def getEncodedBody(self):
        encoding = self.Encoding or "utf-8"
        return ET.tostring(self.DocTree,
            encoding=encoding,
            doctype="<!DOCTYPE html>",
            method="html"
        )


class TextMessage(Message):
    """
    Represent a plain-text message. *contents* must be either a string (which
    must be convertible into unicode using the default encoding) or a unicode
    instance.
    """

    def __init__(self, contents, **kwargs):
        super(TextMessage, self).__init__(ContentTypes.plainText, **kwargs)
        self.Contents = contents

    @property
    def Contents(self):
        """
        Contents of the plain text message. Assigning to this property will
        convert the assigned value to unicode if neccessary and fail for
        anything which does not inherit from str or unicode.
        """
        return self._contents

    @Contents.setter
    def Contents(self, value):
        if isinstance(value, str):
            self._contents = value.decode()
        elif isinstance(value, unicode):
            self._contents = value
        else:
            raise TypeError("TextMessage contents must be string-like.")

    def getEncodedBody(self):
        return self._contents.encode(self.Encoding)
