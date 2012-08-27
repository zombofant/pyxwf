###################
PyWebXML user guide
###################

PyWebXML is the format PyXWF natively understands and uses as intermediate
representation for all transformations after the initial loading of a document
and before the output as (X)HTML.

The PyWebXML namespace has the URI
``http://pyxwf.zombofant.net/xmlns/documents/pywebxml`` assigned and is commonly
used with the prefix ``py:``. In this document, we'll leave out the prefix for
the sake of readibility.

************************
Document type definition
************************

As the name suggests, a PyWebXML document is an XML document. We have not
written a fully specified Document Type Definition yet, but it boils down to
the following:

*   ``<page />`` **must** be the root element of a PyWebXML document.
*   It **must** contain exactly one ``<meta />`` and ``<h:body />``.

``<meta />`` contents
=====================

The following nodes are supported in ``<meta />`` by the default PyWebXML
parser:

*   ``<author />`` (zero or more)

    **Attributes:**

    :@id: *string* – (optional) Reference to another ``<author />`` object
    :@email: *email address* — (optional) e-mail address of the author
    :@href: *url* — (optional) Home page or descriptive website of the author

    **Text content:** Full name (or display name) of the author

    If ``@id`` is set, ``@email`` and ``@href`` will be overwritten by any
    values present in the author declaration in the sitemap with the respective
    ``@id`` in the last transformation stage.

    Stored as list of :class:`~PyXWF.Document.Document.Author` instances
    in the :attr:`~PyXWF.Document.Document.authors` attribute of the resulting
    document and may be used in templates.

*   ``<license />`` (zero or one)

    **Attributes:**

    :@name: *string* — Short name for the license
    :@href: *url* — (optional) URL to a descriptive website of the license
    :@img-href: *url* — (optional) URL to a descriptive image of the license

    **Text content:** Long description of the license

    Stored as :class:`~PyXWF.Document.Document.License` instance in the
    :attr:`~PyXWF.Document.Document.license` attribute of the resulting document
    and may be used in templates.

*   ``<kw />`` (zero or more)

    **Attributes:** None

    **Text content:** Descriptive keyword for the document

    Stored as a list of strings in the :attr:`~PyXWF.Document.Document.keywords`
    attribute of the resulting document and may be used in templates.

*   ``<date />`` (zero or one, required by the blog)

    **Attributes:** None

    **Text content:** Date+Time in the ISO format ``YYYY-MM-DD"T"HH:MM:SS"Z"``.

    Should refer to the date of creation of the document. Stored as :class:`datetime.datetime` object in the
    :attr:`~PyXWF.Document.Document.date` attribute. This is required by the
    Blog, as it uses it for sorting entries.

*   ``<link />`` (zero or more)

    **Attributes:** (in addition to attributes for ``<h:link />``)

    :@rel: *string* — (in addition to ``@rel`` in ``<h:link />``) Can be "script"
    :@ie-only: *string* — (only for ``@rel`` equal to ``"stylesheet"``) Browser switch for MSIE browers

    If ``@rel`` equals to ``"script"``, the element will be converted into a
    respective ``<h:script />`` element.

    If ``@ie-only`` is set, the link will be transformed into an appropriate
    browser switch using the contents of the attribute as condition.

*   ``<h:meta />`` (zero or one)

    Attributes and textual content refer to XHTML specification.

    Stored as list of Element Tree nodes in the
    :attr:`~PyXWF.Document.Document.hmeta` attribute and may be used in
    templates.

Additional elements are stashed away as iterable in the
:attr:`~PyXWF.Document.Document.ext` attribute.
