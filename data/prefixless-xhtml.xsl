<xsl:stylesheet version="1.0"
        xmlns="http://www.w3.org/1999/xhtml"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="no"/>

    <!-- identity transform for everything else -->
    <xsl:template match="/|comment()|processing-instruction()|*|@*">
        <xsl:copy>
          <xsl:apply-templates />
        </xsl:copy>
    </xsl:template>

    <!-- remove NS from XHTML elements -->
    <xsl:template match="*[namespace-uri() = 'http://www.w3.org/1999/xhtml']">
        <xsl:element name="{local-name()}">
          <xsl:apply-templates select="@*|node()" />
        </xsl:element>
    </xsl:template>

    <!-- remove NS from XHTML attributes -->
    <xsl:template match="@*[namespace-uri() = 'http://www.w3.org/1999/xhtml']">
        <xsl:attribute name="{local-name()}">
          <xsl:value-of select="." />
        </xsl:attribute>
    </xsl:template>
</xsl:stylesheet>
