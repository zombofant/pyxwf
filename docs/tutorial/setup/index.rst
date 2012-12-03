****************
Setting up PyXWF
****************

PyXWF currently requires a dedicated webserver with
`WSGI <http://www.python.org/dev/peps/pep-3333/>`_ support. Many widely-used
webservers (at least Apache and lighttpd) support WSGI using a module.

In addition to the python code, you'll have a repository with content, which is
where you put all the data which belongs to the site. We call this the
*data directory*, while the directory where PyXWF resides is the
*PyXWF directory*.

Creating the sitemap and initial data
=====================================

All those files referenced in this section are available in an example form in
the PyXWF repository, in the subdirectory ``misc/example``. You may use these
as a reference to build your own customized website.

PyXWF requires at least one file, the so called ``sitemap.xml`` (although you
can choose a different name). This is an XML file where the whole configuration
for PyXWF goes. It usually resides in the root of the *data directory*.

This is how a bare ``sitemap.xml`` looks (it won't work)::

    <?xml version="1.0" encoding="utf-8" ?>
    <site   xmlns="http://pyxwf.zombofant.net/xmlns/site"
            xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
            xmlns:dir="http://pyxwf.zombofant.net/xmlns/nodes/directory">
        <meta>
            <title>My fancy PyXWF site</title>
        </meta>
        <plugins>
            <p>PyXWF.Nodes.Directory</p>
        </plugins>
        <tweaks />
        <dir:tree
                id="treeRoot"
                template="templates/default.xsl">
        </dir:tree>
        <crumbs />
    </site>

We'll use this as a basement for our walk through the configuration process.
Before we go on, I'll leave a few words on how we at PyXWF think about XML
namespaces, as what we're doing here may seem a bit weird to you if you know
XML (if you don't, you probably should read up on XML anyways, cause most of
PyXWF happens in XML and Python).

PyXWF is really modular, as you might guess from the snippet above, even the
most basic elements like a directory in a site structure are plugins. To keep
the plugins separated from each other in the sitemap XML, each plugin has to
use its own XML namespace.

This brings you to a dilemma when it comes to find the root of the tree in the
sitemap XML: because you _cannot_ know its namespace. Someone could decide to
put a Transform node at the root or just a single page or a remote redirect.

So we have to scan through the whole ``<site />`` node and find a child with the
XML local-name *tree*. This is the only place in PyXWF itself where the
local-name of a node matters.

The ``@template`` attribute on the ``<dir:tree />`` node by the way states the
default template used to render web pages. We'll talk about templates later,
namely when we create the file referenced there.

Adding a home page
------------------

As mentioned previously, this sitemap will not work in PyXWF. You'll recieve
an error message which tells you that the ``dir:tree`` node needs an index
node.

So let's add one::

        <dir:tree
                id="treeRoot"
                template="templates/default.xsl">
            <page:node  name="" id="home"
                src="home.xml"
                type="application/x-pywebxml" />
        </dir:tree>

This won't work on it's own, we have to add two other things. First, the
``page`` namespace prefix needs to be resolved. We do that by adding the
declaration to the ``<site />`` node::

    <site   xmlns="http://pyxwf.zombofant.net/xmlns/site"
            xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
            xmlns:dir="http://pyxwf.zombofant.net/xmlns/nodes/directory"
            xmlns:page="http://pyxwf.zombofant.net/xmlns/nodes/page">

And we also need to load the plugin by adding another ``<p />`` tag::

        <plugins>
            <p>PyXWF.Nodes.Directory</p>
            <p>PyXWF.Nodes.Page</p>
        </plugins>

Now let's add source file for the home page. As you might guess, the
``@src`` attribute of a ``<page:node />`` references the file in which the
node looks for the source of the document to display. All paths are relative
to the *data directory*. So we create a ``home.xml`` file, which has to look
like this to satisfy the ``application/x-pywebxml`` content type set in
``@type``::

    <?xml version="1.0" encoding="utf-8" ?>
    <page   xmlns="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
            xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml">
        <meta>
            <title>Home page</title>
        </meta>
        <body xmlns="http://www.w3.org/1999/xhtml">
            <header>
                <!-- note that hX tags automatically get transformed to hX+1 tags
                     according to the environment where they're used. -->
                <h1>Welcome to my website!</h1>
            </header>
            <p>I just set up PyXWF and want to play around.</p>
        </body>
    </page>

The root element of a PyWebXML document must be a ``<py:page />`` node in
the namespace given above. We usually choose the ``py:`` prefix to reference
this namespace (for more elements and attributes which can be used in that
namespace have a look at the respective documentation). For more information
about PyWebXML documents see :ref:`<py-namespace>`. The only thing you need
to know now is that you can use arbitary XHTML (and anything you can use in
XHTML) inside the ``<h:body />`` element. It will be displayed on page, a correct
template presumed.

Adding a template
-----------------

Templates in PyXWF are XSL transformations. If you don't know anything about
these, you're probably lost. We cannot help you there, you maybe should get some
resources on these.

I won't paste a whole default template here. Instead, i'll describe in short
what the outermost template must do to create a proper website.

*   The input of the transformation is always a valid ``py:page`` tree.
*   The output of the transformation must be a valid ``py:page`` tree.
*   The ``h:body`` of the ``py:page`` tree should contain the whole body which
    should appear in the HTML output.
*   The ``py:meta`` element should contain a ``py:title`` element which will map
    to the HTML title.
*   The ``py:meta`` element can also contain as many ``py:link`` and
    ``h:meta`` elements neccessary to describe your page. Please see the
    ``py:link`` documentation on how to include javascript files.


Setting up WSGI
===============

As mentioned before, PyXWF connects to the Web using WSGI. Here are the
neccessary configuration steps to get it to work.

Create the WSGI script
----------------------

You may want to have a look at ``misc/examples/pyxwf.py`` from the PyXWF
repository to see how a WSGI script might look. Most important is to set up the
path to the *data directory* properly, and make sure that PyXWF is in your
python path.

We'll go through it here anyways. It's basically a normal python script, which
is set up for use with WSGI (see the
`PEP-3333 <http://www.python.org/dev/peps/pep-3333/>`_ for more info about
WSGI itself). A very simplistic approach might look like this and we'll call
this file **pyxwf.py**::

    #!/usr/bin/python2
    # encoding=utf-8
    from __future__ import unicode_literals, print_function

    import sys
    import os
    import logging

    # you can configure logging here as you wish. This is the recommended
    # configuration for testing (disable DEBUG-logging on the cache, it's rather
    # verbose and not particularily helpful at the start)
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("PyXWF.Cache").setLevel(logging.INFO)

    conf = {
        "pythonpath": ["/path/to/pyxwf"],
        "datapath": "/path/to/site"
    }

    try:
        sys.path.extend(conf["pythonpath"])
    except KeyError:
        pass
    os.chdir(conf["datapath"])

    import PyXWF.WebBackends.WSGI as WSGI

    sitemapFile = os.path.join(conf["datapath"], "sitemap.xml")

    application = WSGI.WSGISite(
        sitemapFile,
        default_url_root=conf.get("urlroot")
    )

The *datapath* in the *conf* dictionary refers to the directory in which PyXWF
will look for all files. In fact, all references to files inside the
``sitemap.xml`` are relative to that path. Later on in the snippet above, we
also look for the ``sitemap.xml`` itself in that location. Note that you have
to add the path to the ``PyXWF`` package to your pythonpath (if you have not
already done this globally).

Test it quickly (without dedicated webserver)
---------------------------------------------

For this, PyXWF comes with a script called ``serve.py``. It'll help you to run
test your website as soon as you have a WSGI script running. This will break
though as soon as you have static content which is served from outside of
PyXWF. But for the start, it's fine. It's basic use is pretty simple (and
``./serve.py -h`` will tell you more). Just navigate to the PyXWF directory and
do::

    ./serve.py /path/to/pyxwf.py

(you created the file ``pyxwf.py`` in the previous step!) This will spam some
log messages. After it quiets down, you'll be able to access your site using
the URL http://localhost:8080/.

As soon as you need static files (images, CSS, …), you'll want to use a
dedicated webserver for that, as PyXWF does not deliver such files by default.
The next section deals with setting up PyXWF with Apache, but you're free to
skip this in favour of finding out how awesome PyXWF really is.

You can in fact also run the example delivered with PyXWF using ``serve.py``::

    ./serve.py misc/example/pyxwf.py

``mod_wsgi`` with Apache
------------------------

We are using a configuration similar to this one for zombofant.net::

    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptAlias / /path/to/zombofant/data/pyxwf.py

    # access to static files via Apache, PyXWF won't do that
    Alias /css /path/to/zombofant/data/css
    Alias /img /path/to/zombofant/data/img

Actually, thats all you need. Read up on
`WSGI configuration <https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide>`_
to see how to adapt this to your needs if it doesn't work out of the box.

Before you cheer in happiness, a word of warning. The directive
``WSGIApplicationGroup`` is required for PyXWF to work properly with ``lxml``,
but may also break having multiple PyXWF sites on one server. The solution
is to use one ``WSGIProcessGroup`` for each site. I might write another section
about this, but for the basic setup the above snippet is okay, so I'll leave
that for later.
