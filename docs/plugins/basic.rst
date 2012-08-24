*************************
Basic (every-day) plugins
*************************

These are the plugins one inevitably needs to build a web presence.

:mod:`PyXWF.Nodes.Page` — A static page
=======================================

Namespace: ``http://pyxwf.zombofant.net/xmlns/nodes/page``, prefix ``page:``

*   *tree node*: ``<page:node />``

    **Attributes:**

    :@src: *file name*: The file containing the source of the document which should be rendered.
    :@type: *mime type*: MIME type of the source file.

    **Compatible child nodes:** None

The node returns the document from ``@src`` on every *GET* request. Other
requests are not supported. To load the document, a parser for the MIME type
specified at ``@type`` has to be loaded at the current site.

:mod:`PyXWF.Nodes.Directory` — A directory of nodes
===================================================

Namespace: ``http://pyxwf.zombofant.net/xmlns/nodes/directory``, prefix: ``dir:``

*   *tree node*: ``<dir:node />``

    **Attributes:** None

    **Compatible child nodes:** All *tree nodes*

*   *root node*: ``<dir:tree />``

    **Attributes:** None

    **Compatible child nodes:** All *tree nodes*

The nodes represents a directory of tree nodes which can be accessed by
appending their ``@name`` to the path of the directory node, separated by a
``/``. If a name is requested which does not match the name of any child node,
a :cls:`PyXWF.Errors.HTTP.NotFound` error is raised.

``<dir:node />`` and ``<dir:tree />`` nodes **require** a child node whose
``@name`` is the empty string (or unset).

The ``<dir:tree />`` node works the same like ``<dir:node />``, but can only
be placed at the tree root.

:mod:`PyXWF.Nodes.Redirect` — Place a redirect
==============================================

Namespace: ``http://pyxwf.zombofant.net/xmlns/nodes/redirect``, prefix: ``redirect:``

*   *tree node*: ``<redirect:internal />``

    **Attributes:**

    :@to: *tree node id*: ID of the node to redirect to
    :@method: *redirect method*: The (HTTP-)method to use for the redirect
    :@cachable: *boolean*: Whether the redirect should be made cachable.

    **Compatible child nodes:** None

.. _redirect-method-values:

Valid values for a *redirect method* are:

:found: *(default)*: HTTP ``302 Found`` status code
:see-other: HTTP ``303 See Other`` status code
:moved-permanently: HTTP ``301 See Other`` status code
:temporary-redirect: HTTP ``307 Temporary Redirect`` status code
:internal: No HTTP response is sent (yet). Instead, PyXWF is internally redirected to the resource specified by ``@to``.

When the node is hit during path resolution and ``@method`` is *internal*,
the node behaves as if it was the node referred to by ``@to``. Otherwise, the
redirect node is returned.

Any HTTP request made to a redirect node (which, by definition has a
``@method`` not equal to *internal*, otherwise the request would *internally*
be redirected to the target node), the appropriate HTTP status code is set and
the absolute URI pointing to the node referred to by ``@to`` is set as the value
of the HTTP ``Location`` header. When doing this, the URL scheme used for the
request is kept and the host name sent in the ``Host`` header is used.
