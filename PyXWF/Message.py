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
    the :meth:`get_encoded_body` method.

    It handles sending the message in a given transaction context if all
    properties and methods are set up properly.

    *mimetype* is the MIME type according to RFC 2046.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, mimetype, status=Errors.OK, encoding=None):
        super(Message, self).__init__()
        self._mimetype = mimetype
        self._encoding = encoding
        self._last_modified = None
        self._status = status

    @property
    def MIMEType(self):
        """
        The internet media type (aka *content type*) of the :class:`~Message`.
        """
        return self._mimetype

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
    def get_encoded_body(self):
        """
        Return the bytes object resembling the contents encoded in the encoding
        set up in :attr:`Encoding`.

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
                    self._mimetype == other._mimetype and
                    self.get_encoded_body() == other.get_encoded_body())
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
            self._mimetype,
            self._encoding,
            self.get_encoded_body(),
            self._last_modified.isoformat() if self._last_modified else "None"
        )

    def __repr__(self):
        return str(self)


class XMLMessage(Message):
    """
    Represent a generic XML message. *doctree* must be a valid lxml Element or
    ElementTree. *content_type* must specify the MIME type of the document.

    If cleanup_namespaces is True, :func:`lxml.etree.cleanup_namespaces` will be
    called on the tree.
    """

    def __init__(self, doctree, content_type, cleanup_namespaces=False,
            pretty_print=False, force_namespaces={}, **kwargs):
        super(XMLMessage, self).__init__(content_type, **kwargs)
        self._doctree = doctree
        self._pretty_print = pretty_print
        if cleanup_namespaces:
            try:
                # this is only available with lxml backend
                ET.cleanup_namespaces(self._doctree)
            except AttributeError:
                pass
        if force_namespaces:
            root = self._doctree.getroot()
            # this is an ugly hack
            nsmap = root.nsmap
            nsmap.update(force_namespaces)
            newroot = ET.Element(root.tag, attrib=root.attrib, nsmap=nsmap)
            newroot.extend(root)
            self._doctree = ET.ElementTree(newroot)
            """for prefix, uri in force_namespaces.viewitems():
                root.set("{{{0}}}{1}".format("http://www.w3.org/2000/xmlns/", prefix), uri)"""
    @property
    def DocTree(self):
        return self._doctree

    @DocTree.setter
    def DocTree(self, value):
        self._doctree = value

    def get_encoded_body(self, **kwargs):
        simpleargs = {
            "encoding": self.Encoding or "utf-8",
            "xml_declaration": "yes",
            "pretty_print": self._pretty_print
        }
        simpleargs.update(kwargs)
        return ET.tostring(self.DocTree,
            **simpleargs
        )

class XHTMLMessage(XMLMessage):
    """
    Represent an XHTML message. *doctree* must be a valid XHTML document tree
    as lxml.etree node. Conversion to bytes payload is handled by this class
    automatically.
    """

    def __init__(self, doctree, minify_namespaces=True,
            **kwargs):
        myargs = {
            "cleanup_namespaces": True
        }
        myargs.update(kwargs)
        super(XHTMLMessage, self).__init__(doctree, ContentTypes.xhtml,
            **myargs)
        self._minify_namespaces = minify_namespaces

    def get_encoded_body(self):
        kwargs = {
            "doctype": "<!DOCTYPE html>"
        }
        return super(XHTMLMessage, self).get_encoded_body(**kwargs)


class HTMLMessage(Message):
    """
    Represent an HTML message. *doctree* must be a valid HTML document tree
    (the same as the XHTML tree, but without namespaces) as lxml.etree node.
    Conversion to bytes payload is handled by this class automatically.

    You can specify the HTML version via *version*, which is currently
    restricted to `HTML5`.
    """

    @classmethod
    def from_xhtml_tree(cls, doctree, version="HTML5", **kwargs):
        """
        Return an :class:`~HTMLMessage` instance from the given XHTML *doctree*.
        This performs automatic conversion by removing the XHTML namespace from
        all elements. Raises :class:`ValueError` if a non-xhtml namespace is
        encountered.
        """
        doctree = copy.copy(doctree)
        utils.XHTMLToHTML(doctree)
        try:
            # this is only available with lxml backend
            ET.cleanup_namespaces(doctree)
        except AttributeError:
            pass
        return cls(doctree, version=version, **kwargs)

    def __init__(self, doctree, version="HTML5", pretty_print=False, **kwargs):
        if version != "HTML5":
            raise ValueError("Invalid HTMLMessage version: {0}".format(version))
        super(HTMLMessage, self).__init__(ContentTypes.html, **kwargs)
        self._doctree = doctree
        self._pretty_print = pretty_print

    @property
    def DocTree(self):
        return self._doctree

    @DocTree.setter
    def DocTree(self, value):
        self._doctree = value

    def get_encoded_body(self):
        encoding = self.Encoding or "utf-8"
        return ET.tostring(self.DocTree,
            encoding=encoding,
            doctype="<!DOCTYPE html>",
            method="html",
            pretty_print=self._pretty_print
        )


class TextMessage(Message):
    """
    Represent a plain-text message. *contents* must be either a string (which
    must be convertible into unicode using the default encoding) or a unicode
    instance.
    """

    def __init__(self, contents, **kwargs):
        super(TextMessage, self).__init__(ContentTypes.plaintext, **kwargs)
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

    def get_encoded_body(self):
        return self._contents.encode(self.Encoding)


class EmptyMessage(Message):
    """
    Represent a message without a body.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("status", Errors.NoContent)
        super(EmptyMessage, self).__init__(None, **kwargs)

    def get_encoded_body(self):
        return None
