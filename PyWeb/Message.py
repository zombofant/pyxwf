import abc

from WebStack.Generic import Transaction, ContentType


import PyWeb.ContentTypes as ContentTypes
from PyWeb.utils import ET

class MessageInfo(object):
    def __init__(self, wsContentType, contentBytes):
        super(MessageInfo, self).__init__()
        self.wsContentType = wsContentType
        self.contentBytes = contentBytes

    def applyToTransaction(self, transaction):
        transaction.rollback()
        transaction.set_content_type(self.wsContentType)
        transaction.get_response_stream().write(self.contentBytes)


class Message(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, mimeType):
        super(Message, self).__init__()
        self._mimeType = mimeType
        self._encoding = None

    @property
    def MIMEType(self):
        return self._mimeType

    @property
    def Encoding(self):
        return self._encoding

    @Encoding.setter
    def Encoding(self, value):
        self._encoding = value

    @abc.abstractmethod
    def getEncodedBody(self):
        pass

    def getMessageInfo(self):
        return MessageInfo(
            ContentType(self.MIMEType, self.Encoding),
            self.getEncodedBody()
        )


class XHTMLMessage(Message):
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
    def __init__(self, contents):
        super(TextMessage, self).__init__(ContentTypes.plainText)
        self._contents = unicode(contents)

    @property
    def Contents(self):
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
