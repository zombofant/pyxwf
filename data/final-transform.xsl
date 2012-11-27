<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:localr="http://pyxwf.zombofant.net/xmlns/href/localr"
        xmlns:localg="http://pyxwf.zombofant.net/xmlns/href/localg">
    <xsl:output method="xml" encoding="utf-8" />
    <xsl:strip-space elements="py:if py:then py:else" />

    <xsl:variable name="localr">http://pyxwf.zombofant.net/xmlns/href/localr</xsl:variable>
    <xsl:variable name="localg">http://pyxwf.zombofant.net/xmlns/href/localg</xsl:variable>
    <xsl:variable name="py">http://pyxwf.zombofant.net/xmlns/documents/pywebxml</xsl:variable>

    <!-- library for boolean checks and py:if in general -->

    <xsl:template name="py-cond-true">
        <xsl:apply-templates select="py:then/@*|py:then/node()" />
    </xsl:template>

    <xsl:template name="py-cond-false">
        <xsl:apply-templates select="py:else/@*|py:else/node()" />
    </xsl:template>

    <xsl:template name="py-bool-check">
        <xsl:param name="reference" />
        <xsl:param name="attrib" />
        <!-- convert a string representing a boolean to a boolean -->
        <!-- 'true', 'yes' and '1' are true values, everything else maps to false -->
        <xsl:variable name="battrib" select="
            boolean(translate(string($attrib), 'TRUE', 'true') = 'true' or
            string($attrib) = '1' or
            translate(string($attrib), 'YES', 'yes') = 'yes')" />
        <xsl:choose>
            <xsl:when test="$battrib = boolean($reference)">
                <xsl:call-template name="py-cond-true" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="py-cond-false" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="py-transform-localr-href">
        <xsl:param name="href" select="@href" />
        <xsl:choose>
            <xsl:when test="starts-with(string($href), '/')">
                <xsl:value-of select="$href" />
            </xsl:when>
            <xsl:when test="starts-with(string($href), '#')">
                <xsl:value-of select="$href" />
            </xsl:when>
            <xsl:when test="contains(string($href), '://')">
                <xsl:value-of select="$href" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$url_root" />
                <xsl:value-of select="$href" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="py-host-prefix">
        <xsl:value-of select="$url_scheme" />
        <xsl:text>://</xsl:text>
        <xsl:value-of select="$host_name" />
    </xsl:template>

    <xsl:template name="py-transform-localg-href">
        <xsl:param name="href" select="@href" />
        <xsl:choose>
            <xsl:when test="starts-with(string($href), '/')">
                <xsl:call-template name="py-host-prefix" />
                <xsl:value-of select="$href" />
            </xsl:when>
            <xsl:when test="starts-with(string($href), '#')">
                <xsl:value-of select="$href" />
            </xsl:when>
            <xsl:when test="contains(string($href), '://')">
                <xsl:value-of select="$href" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="py-host-prefix" />
                <xsl:value-of select="$url_root" />
                <xsl:value-of select="$href" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- transforms to apply -->

    <!-- identity transform for all unknown elements-->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- localr: namespaced attributes -->
    <xsl:template match="@*[namespace-uri() = 'http://pyxwf.zombofant.net/xmlns/href/localr']">
        <xsl:attribute name="{local-name()}">
            <xsl:call-template name="py-transform-localr-href">
                <xsl:with-param name="href" select="." />
            </xsl:call-template>
        </xsl:attribute>
    </xsl:template>

    <!-- localg: namespaced attributes -->
    <xsl:template match="@*[namespace-uri() = 'http://pyxwf.zombofant.net/xmlns/href/localg']">
        <xsl:attribute name="{local-name()}">
            <xsl:call-template name="py-transform-localg-href">
                <xsl:with-param name="href" select="." />
            </xsl:call-template>
        </xsl:attribute>
    </xsl:template>

    <!-- <py:if mobile /> -->
    <xsl:template match="py:if[@py:mobile]">
        <xsl:call-template name="py-bool-check">
            <xsl:with-param name="reference" select="$deliver_mobile" />
            <xsl:with-param name="attrib" select="@py:mobile" />
        </xsl:call-template>
    </xsl:template>

    <!-- @py:drop-empty -->
    <xsl:template match="node()[@py:drop-empty]">
        <xsl:choose>
            <xsl:when test="count(*) &gt; 0">
                <xsl:copy>
                    <xsl:apply-templates select="@*[namespace-uri() != $py]|node()" />
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- legacy: <py:a />, <py:link /> -->
    <xsl:template match="py:a | py:link">
        <xsl:element name="h:{local-name(.)}">
            <xsl:if test="@href">
                <xsl:attribute name="href">
                    <xsl:call-template name="py-transform-localr-href" />
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates select="@*[local-name() != 'href']|node()" />
        </xsl:element>
    </xsl:template>

    <!-- legacy: <py:script /> -->
    <xsl:template match="py:script">
        <xsl:element name="h:script">
            <xsl:if test="@href">
                <xsl:attribute name="src">
                    <xsl:call-template name="py-transform-localr-href" />
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates select="@*[local-name() != 'href']|node()" />
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- legacy <py:img /> -->
    <xsl:template match="py:img">
        <h:img>
            <xsl:if test="@href">
                <xsl:attribute name="src">
                    <xsl:call-template name="py-transform-localr-href" />
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates select="@*[local-name() != 'href' and local-name() != 'src']|node()" />
        </h:img>
    </xsl:template>

    <!-- legacy @py:content -->
    <xsl:template match="@py:content-make-uri"></xsl:template>

    <xsl:template match="@py:content">
        <xsl:attribute name="content">
            <xsl:choose>
                <xsl:when test="string(../@py:content-make-uri) = 'true'">
                    <xsl:call-template name="py-transform-localg-href">
                        <xsl:with-param name="href" select="." />
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="py-transform-localr-href">
                        <xsl:with-param name="href" select="." />
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
    </xsl:template>

    <!-- legacy <py:if-mobile /> -->
    <xsl:template name="py-legacy-if-mobile-subtree">
        <xsl:apply-templates select="@*[local-name() != 'mobile' and local-name() != 'xhtml-element']|node()" />
    </xsl:template>

    <xsl:template match="py:if-mobile">
        <xsl:choose>
            <xsl:when test="((@mobile = 'true' or not(@mobile)) and $deliver_mobile) or (@mobile = 'false' and not($deliver_mobile))">
                <xsl:choose>
                    <xsl:when test="@xhtml-element">
                        <xsl:element name="h:{@xhtml-element}">
                            <xsl:call-template name="py-legacy-if-mobile-subtree" />
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <h:span>
                            <xsl:call-template name="py-legacy-if-mobile-subtree" />
                        </h:span>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
