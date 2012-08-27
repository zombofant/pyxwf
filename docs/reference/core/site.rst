:mod:`PyXWF.Site` — A whole Website
===================================

.. automodule:: PyXWF.Site
    :members:

.. _site-hooks:

Hooks available on :class:`~PyXWF.Site.Site` objects
---------------------------------------------------

The following hooks are available on every :class:`~PyXWF.Site.Site` instance.
They're called with the specified arguments and their return value is ignored.
See :class:`PyXWF.Registry.HookRegistry` for more information on hooking.

.. currentmodule:: None

.. function:: tweaks-loaded()

    All nodes in ``<site:tweaks />`` have been processed. This is
    useful to do something smart with the configuration you received.

.. function:: tree-loaded()

    The tree root has been found in the sitemap and is completely
    loaded. This implies that all node IDs are accessible by the time this
    hook is called.

.. function:: crumbs-loaded()

    The whole ``<site:crumbs />`` has been processed.

.. function:: loading-finished()

    The whole sitemap was successfully processed.

.. function:: handle.pre-lookup(ctx)

    :meth:`~PyXWF.Site.Site.getMessage` has just been called, no lookup has
    been done yet. This is useful to place site-wide redirects.

    *ctx* is the :class:`~PyXWF.Context.Context` instance of the request.
