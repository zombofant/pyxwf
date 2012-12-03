<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <xsl:output method="xml" encoding="utf-8" />

    <!-- identity transform -->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="py:page">
        <py:page>
            <py:meta>
                <py:title><xsl:value-of select="$doc_title" /> • <xsl:value-of select="$site_title" /></py:title>
                <!-- you could add some global stylesheets or scripts here -->
                <h:meta name="title" content="{$doc_title}" />
            </py:meta>
            <body xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
                <h1>PyXWF Example</h1>
                <a id="content" />
                <xsl:copy-of select="h:body/@*" />
                <xsl:apply-templates select="h:body/*" />
            </body>
        </py:page>
    </xsl:template>
</xsl:stylesheet>
