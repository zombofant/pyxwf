<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <xsl:output method="xml" encoding="utf-8" />

    <xsl:template name="py-author-email">
        <xsl:param name="value" select="." />
        <xsl:param name="addr" select="@email" />
        <xsl:param name="tag-name" select="1" />
        <h:a property="email" href="mailto:{$addr}" content="{$addr}">
            <h:span>
                <xsl:if test="$tag-name">
                    <xsl:attribute name="property">name</xsl:attribute>
                </xsl:if>
                <xsl:value-of select="$value" />
            </h:span>
        </h:a>
    </xsl:template>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="py:author">
        <h:span typeof="Person" property="author">
            <xsl:choose>
                <xsl:when test="@href">
                    <py:a property="url">
                        <xsl:attribute name="href">
                            <xsl:value-of select="href" />
                        </xsl:attribute>
                        <h:span property="name"><xsl:value-of select="." /></h:span>
                    </py:a>
                    <xsl:if test="@email">
                        <xsl:call-template name="py-author-email">
                            <xsl:with-param name="value" value="✉" />
                            <xsl:with-param name="tag-name" value="0" />
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="@email">
                    <xsl:call-template name="py-author-email" />
                </xsl:when>
                <xsl:otherwise>
                    <h:span property="name"><xsl:value-of select="." /></h:span>
                </xsl:otherwise>
            </xsl:choose>
        </h:span>
    </xsl:template>

    <xsl:template name="py-license-img-name">
        <xsl:param name="license" select="." />
        <xsl:choose>
            <xsl:when test="@img-href">
                <py:img>
                    <xsl:attribute name="href">
                        <xsl:value-of select="@img-href" />
                    </xsl:attribute>
                    <xsl:attribute name="title">
                        <xsl:value-of select="@name" />
                        <xsl:if test="string($license)"
                            xml:space="preserve">: <xsl:value-of select="$license" /></xsl:if>
                    </xsl:attribute>
                    <xsl:attribute name="alt">
                        <xsl:value-of select="@name" />
                    </xsl:attribute>
                </py:img>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="title"><xsl:value-of select="$license" /></xsl:attribute>
                <xsl:value-of select="@name" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="py:license">
        <xsl:choose>
            <xsl:when test="@href">
                <py:a class="license" rel="license" property="dc:license">
                    <xsl:attribute name="href"><xsl:value-of select="@href" /></xsl:attribute>
                    <xsl:call-template name="py-license-img-name" />
                </py:a>
            </xsl:when>
            <xsl:otherwise>
                <h:span class="license"><xsl:call-template name="py-license-img-name" /></h:span>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="py:page">
        <py:page>
            <py:meta>
                <py:title><xsl:value-of select="$doc_title" /> • <xsl:value-of select="$site_title" /></py:title>
                <py:link rel="stylesheet" type="text/css" href="css/screen.css" media="screen, projection" />
                <py:link rel="stylesheet" type="text/css" href="css/print.css" media="print" />
                <py:link rel="stylesheet" type="text/css" href="css/main.css" media="screen, projection" />
                <xsl:copy-of select="py:meta/py:link" />
                <xsl:copy-of select="py:meta/py:kw" />
                <xsl:copy-of select="py:meta/h:meta" />
                <h:meta name="title" content="{$doc_title}" />
            </py:meta>
            <body xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en" vocab="http://schema.org/">
                <section class="bp-container root" typeof="WebPage">
                    <header class="bp-span-24 bp-last bp-first">
                        <py:a href="" accesskey="1"
                                class="home bp-span-16 bp-first"
                                property="url"
                                py:content=""
                                py:content-make-uri="true">
                            <h1 property="headline">
                                <xsl:value-of select="$site_title" />
                            </h1>
                            <span property="additionalHeadline">hacking and stuff</span>
                        </py:a>
                        <div class="bp-span-8 bp-last hashlinks">
                            <a href="#content" accesskey="2">#skip-to-content</a><br />
                            <a href="#main-nav" accesskey="5">#navigation</a>
                        </div>
                    </header>
                    <article id="main-content"
                            class="bp-column bp-span-14 bp-prepend-5 bp-append-5 bp-alt">
                        <nav class="bread">You are here: <py:crumb id="bread" /></nav>
                        <a id="content" />
                        <xsl:copy-of select="h:body/@*" />
                        <xsl:apply-templates select="h:body/*" />
                    </article>
                    <aside  class="bp-column bp-span-5 bp-pull-24 main-nav">
                        <header>
                            <h2>Navigation</h2>
                        </header>
                        <a id="main-nav" />
                        <nav class="main">
                            <py:crumb id="nav-meta" />
                        </nav>
                        <nav class="main">
                            <py:crumb id="nav-blog" />
                        </nav>
                        <nav class="main">
                            <py:crumb id="nav-hacking" />
                        </nav>
                        <!--<section class="tagcloud">
                            <header>
                                <h3>Tag cloud</h3>
                            </header>
                            <py:crumb id="tagcloud" />
                        </section>-->
                    </aside>
                    <footer class="bp-span-24 bp-last">
                        <!-- <xsl:if test="py:meta/py:author">
                            <ul class="authors">
                                <xsl:for-each select="py:meta/py:author">
                                    <li><xsl:apply-templates select="." /></li>
                                </xsl:for-each>
                            </ul>
                        </xsl:if>-->
                        <div class="bp-prepend-3 bp-span-18 bp-append-3 bp-last">
                            The content on this page is licensed under <xsl:apply-templates select="py:meta/py:license" />. <br />
                            <py:a href="meta/about">About us</py:a> • <py:a href="meta/legal-notes" accesskey="8">Legal notes / Impressum</py:a> • <py:a href="meta/accessibility-statement" accesskey="0">Accessibility</py:a>
                        </div>
                    </footer>
                </section>
            </body>
        </py:page>
    </xsl:template>
</xsl:stylesheet>
