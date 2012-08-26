"""
In PyXWF, we call all content we send over the wire a Message. Messages thus
contain information about their mime type, encoding and of course their payload.

They represent it internally however they like, but must be able to serialize
the payload to a properly encoded bytes object for conversion in a MessageInfo
instance.
"""

import abc, copy

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Errors as Errors

class Message(object):
    """
    Baseclass for any message. For proper function, messages must implement
    the :meth:`getEncodedBody` method.

    It handles sending the message in a given transaction context if all
    properties and methods are set up properly.

    *mimeType* is the MIME type according to RFC 2046.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, mimeType, status=Errors.OK, encoding=None):
        super(Message, self).__init__()
        self._mimeType = mimeType
        self._encoding = encoding
        self._lastModified = None
        self._status = status

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
        return self._status.code

    @property
    def Status(self):
        return self._status

    @Status.setter
    def Status(self, value):
        self._status = value

    def __eq__(self, other):
        try:
            return (self._status.code == other._status.code and
                    self._encoding == other._encoding and
                    self._mimeType == other._mimeType and
                    self.getEncodedBody() == other.getEncodedBody())
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        result = self == other
        if result is NotImplemented:
            return result
        return not result

    def __str__(self):
        return """\
{0} {1}
Content-Type: {2}; charset={3}
Last-Modified: {5}

{4}\n""".format(
            self._status.code,
            self._status.title,
            self._mimeType,
            self._encoding,
            self.getEncodedBody(),
            self._lastModified.isoformat() if self._lastModified else "None"
        )

    def __repr__(self):
        return str(self)


class XMLMessage(Message):
    """
    Represent a generic XML message. *docTree* must be a valid lxml Element or
    ElementTree. *contentType* must specify the MIME type of the document.

    If cleanupNamespaces is True, :func:`lxml.etree.cleanup_namespaces` will be
    called on the tree.
    """

    def __init__(self, docTree, contentType, cleanupNamespaces=False,
            prettyPrint=False, forceNamespaces={}, **kwargs):
        super(XMLMessage, self).__init__(contentType, **kwargs)
        self._docTree = docTree
        self._prettyPrint = prettyPrint
        if cleanupNamespaces:
            try:
                # this is only available with lxml backend
                ET.cleanup_namespaces(self._docTree)
            except AttributeError:
                pass
        if forceNamespaces:
            root = self._docTree.getroot()
            # this is an ugly hack
            nsmap = root.nsmap
            nsmap.update(forceNamespaces)
            newRoot = ET.Element(root.tag, attrib=root.attrib, nsmap=nsmap)
            newRoot.extend(root)
            self._docTree = ET.ElementTree(newRoot)
            """for prefix, uri in forceNamespaces.viewitems():
                root.set("{{{0}}}{1}".format("http://www.w3.org/2000/xmlns/", prefix), uri)"""
    @property
    def DocTree(self):
        return self._docTree

    @DocTree.setter
    def DocTree(self, value):
        self._docTree = value

    def getEncodedBody(self, **kwargs):
        simpleArgs = {
            "encoding": self.Encoding or "utf-8",
            "xml_declaration": "yes",
            "pretty_print": self._prettyPrint
        }
        simpleArgs.update(kwargs)
        return ET.tostring(self.DocTree,
            **simpleArgs
        )

class XHTMLMessage(XMLMessage):
    """
    Represent an XHTML message. *docTree* must be a valid XHTML document tree
    as lxml.etree node. Conversion to bytes payload is handled by this class
    automatically.
    """

    def __init__(self, docTree, minifyNamespaces=True,
            **kwargs):
        myArgs = {
            "cleanupNamespaces": True
        }
        myArgs.update(kwargs)
        super(XHTMLMessage, self).__init__(docTree, ContentTypes.xhtml,
            **myArgs)
        self._minifyNamespaces = minifyNamespaces

    def getEncodedBody(self):
        kwargs = {
            "doctype": "<!DOCTYPE html>"
        }
        return super(XHTMLMessage, self).getEncodedBody(**kwargs)


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

    def __init__(self, docTree, version="HTML5", prettyPrint=False, **kwargs):
        if version != "HTML5":
            raise ValueError("Invalid HTMLMessage version: {0}".format(version))
        super(HTMLMessage, self).__init__(ContentTypes.html, **kwargs)
        self._docTree = docTree
        self._prettyPrint = prettyPrint

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
            method="html",
            pretty_print=self._prettyPrint
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


class EmptyMessage(Message):
    """
    Represent a message without a body.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("status", Errors.NoContent)
        super(EmptyMessage, self).__init__(None, **kwargs)

    def getEncodedBody(self):
        return None
