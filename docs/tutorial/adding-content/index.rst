Going on: Adding more content
=============================

Hey, welcome back. Nice to see you made it through the first part of the
tutorial! If you didn't read that yet, I'd recommend you to do so—it introduces
some important concepts.

We'll talk about the basic PyXWF nodes, which are *redirect*, *directory* and
*page*. Those are actually doing exactly what you'd expect. Also we'll talk
about navigations (which are really easy business with PyXWF).

*   A page, as you've seen in the previous part, serves static XHTML [#xhtml]_
    content from a file. Note that the files content doesn't need to be in
    XHTML format—there just needs to be a Parser for it in PyXWF. PyXWF comes
    with parsers for PyWebXML (basically vanilla XHTML with a tiny wrapper)
    and the famous Markdown.
*   A directory is a container for multiple pages, which has its name from the
    fact that it's represented as a directory in the URL.
*   A redirect node allows you to define a redirect inside the PyXWF sitemap
    which will be executed as the appropriate HTTP response (or handled as an
    alias)

To give this all a more aimed touch, we'll imagine the following situation. We
want to start a community website, where we have some projects which we want
to display status of. We also want a small blog where people can post about
their projects. That sounds a lot? It's actually pretty easy to acomplish. In
this section, we'll start with adding generic information about our community.

Adding a directory
------------------

We before had the following sitemap tree::

        <dir:tree
                id="treeRoot"
                template="templates/default.xsl">
            <page:node  name="" id="home"
                src="home.xml"
                type="application/x-pywebxml" />
        </dir:tree>



.. rubric:: Footnotes

.. [#xhtml] Why XHTML? XHTML is a reasonable (the only, if you'd ask me) way to
    represent HTML data. The great advantage we get from using XHTML content
    internally is that we have a coherent document tree, can embed XHTML in
    other formats (PyWebXML for example) and apply XSL transformations to it.

    But you know what's even better? PyXWF makes sure **browsers can read your
    XHTML**! It'll downconvert it to HTML whenever neccessary, by using
    `Content Negotiation <https://en.wikipedia.org/wiki/Content_negotiation>`_
    and wild guesses about the User Agent.
