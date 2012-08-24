****************
Advanced plugins
****************

These plugins are usually not neccessary for a normal website, but we found them
useful for our own projects.

:mod:`PyXWF.Nodes.MirrorSwitch` — Redirect to random mirror
===========================================================

Namespace: ``http://pyxwf.zombofant.net/xmlns/nodes/mirror-switch``, prefix: ``mirror``

*   *tree node*: ``<mirror:switch />``

    **Attributes**: None

    **Compatible child nodes**: one or more ``<mirror:host />``

*   *mirror host node*: ``<mirror:host />``

    **Attributes**:

    :@host: *host name* — Host name of the mirror server
    :@path: *url path* — Path on the mirror servers host
    :@port: *port number* — (optional; defaults to *80*) Port to use for HTTP
    :@ssl-port: *port number* — (optional; defaults to *443*) Port to use for HTTPS
    :@no-ssl: *boolean* — (optional; defaults to *False*) Disable SSL for the host

    **Allowed child nodes**: None

If path resolving hits the ``<mirror:switch />`` tree node, an HTTP redirect
(``302 Found``) to a semi-random mirror is issued. The mirror is picked based
on the following algorithm:

*   Take the list of all mirrors and shuffle it
*   For each mirror:

    *   Send a ``HEAD`` request to ``scheme://host:port/path/relpath``, where
        *scheme* is ``https`` if ``@no-ssl`` is False, ``http`` otherwise,
        *host* is the value of ``@host``, *port* the respective port number,
        *path* the ``@path`` value and *relpath* the path of the
        initial request, relative to the switch node.
    *   If that request returns a ``200 OK``, exit with a redirect to the above
        location.
    *   Otherwise, check next mirror

*   If no mirror can serve the file, issue a ``404 Not Found`` response.

Note that this algorithm does by no means make sure that the file served by the
mirror has the expected content. This should only be used with trusted mirrors
and/or the appropriate security means.

:mod:`PyXWF.Nodes.Transform` — Generate content and trees from XSL transformations
==================================================================================

TBD
