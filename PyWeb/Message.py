"""
In PyWeb, we call all content we send over the wire a Message. Messages thus
contain information about their mime type, encoding and of course their payload.

They represent it internally however they like, but must be able to serialize
the payload to a properly encoded bytes object for conversion in a MessageInfo
instance.
"""

import abc

from WebStack.Generic import Transaction, ContentType

import PyWeb.ContentTypes as ContentTypes
from PyWeb.utils import ET

class Message(object):
    """
    Baseclass for any message. For proper function, messages must implement
    the :meth:`getEncodedBody` method.

    It handles sending the message in a given transaction context if all
    properties and methods are set up properly.

    *mimeType* is the MIME type according to RFC 2046.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, mimeType):
        super(Message, self).__init__()
        self._mimeType = mimeType
        self._encoding = None

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

    def sendInTransaction(self, transaction):
        transaction.rollback()
        transaction.set_content_type(ContentType(self.MIMEType, self.Encoding))
        transaction.get_response_stream().write(self.getEncodedBody())

    def sendInContext(self, ctx):
        self.sendInTransaction(ctx.transaction)


class XHTMLMessage(Message):
    """
    Represent an XHTML message. *docTree* must be a valid XHTML document tree
    as lxml.etree node. Conversion to bytes payload is handled by this class
    automatically.
    """
    
    def __init__(self, docTree):
        super(XHTMLMessage, self).__init__(ContentTypes.xhtml)
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
            xml_declaration="yes",
            doctype="<!DOCTYPE html>"
        )


class TextMessage(Message):
    """
    Represent a plain-text message. *contents* must be either a string (which
    must be convertible into unicode using the default encoding) or a unicode
    instance.
    """
    
    def __init__(self, contents):
        super(TextMessage, self).__init__(ContentTypes.plainText)
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
