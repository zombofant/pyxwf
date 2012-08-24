*************************
Tweaks of PyXWF behaviour
*************************

:mod:`PyXWF.Tweaks.Host` — Host based behaviour
===============================================

Namespace: ``http://pyxwf.zombofant.net/xmlns/tweaks/host``, prefix: ``host:``

*   *tweak node* ``<host:redirect />``

    **Occurrence**: zero or more

    **Attributes**:

    :@src: *host name* — Host name to redirect from
    :@dest: *host name* — Host name to redirect to
    :@method: *redirect method* — Method of redirect, see :ref:`Valid values for *redirect methods* <redirect-method-values>`. *internal* is **not allowed**

    **Allowed child nodes:** None

If the current request is issued with the HTTP ``Host`` header equal to a host
given in one of the redirect nodes ``@src`` attributes, an HTTP status code
according to ``@method`` is set and the ``Location`` header is set to the same
absolute URI as the current location, except that the host name is set to the
value of the respective ``@dest`` attribute.


*   *tweak node* ``<host:force-mobile />``

    **Occurence**: zero or more

    **Attributes**:

    :@host: *host name* — Host name to match against
    :@mobile: *boolean* — The value to set the :prop:`PyXWF.Context.IsMobileClient` property to

    **Allowed child nodes:** None

If the current request is issued with the HTTP ``Host`` header equal to a host
given in one of the force-mobile nodes ``@host`` attributes, the value of the
:prop:`PyXWF.Context.IsMobileClient` property is set to the value of the
respective ``@mobile`` attribute.

This is useful to create mobile versions of websites, based on the host name
rather than the user agent. For this to override the User-Agent based detection
completely, you need a ``<host:force-mobile />`` node for each host name the
PyXWF site handles requests for.
