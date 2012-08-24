PyXWF – eXtensible Web Framework Documentation
==============================================

Welcome to the documentation of PyXWF, an extensible web framework for Python.
It is written in pure python, using the *lxml* and *WebStack* libraries.

To learn more about PyXWF, please have a look at
`the official PyXWF page <http://zombofant.net/hacking/pyxwf>`_.

Hints on notation
-----------------

Throughout the documentation, we'll be talking about XML nodes and
attributes. XML nodes are referenced by ``<ns:name />`` or ``ns:name``,
where *ns:* is the namespace prefix (if any) and *name* is the local-name of
the Node. XML attributes are referenced by ``@ns:name``, with *ns:* and
*name* having the same meanings as before.

Some namespaces are used commonly with PyXWF and thus have some prefixes we
consider default and useful:

*  ``h:`` maps to ``http://www.w3.org/1999/xhtml``, the XHTML namespace.
*  ``py:`` maps to ``http://pyxwf.zombofant.net/xmlns/documents/pywebxml``,
   the namespace for PyWebXML documents.

Table of contents
-----------------

.. toctree::
   :maxdepth: 3

   tutorial/index
   plugins/index
   reference/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

