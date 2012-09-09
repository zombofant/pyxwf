<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" encoding="utf-8" />

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template name="to-div">
        <xsl:param name="orig" select="." />
        <xsl:param name="orig-class" select="@class" />
        <xsl:param name="add-class" />
        <h:div>
            <xsl:attribute name="class">
                <xsl:if test="@class">
                    <xsl:value-of select="@class" />
                    <xsl:value-of select="' '" />
                </xsl:if>
                <xsl:value-of select="$add-class" />
            </xsl:attribute>
            <xsl:for-each select="@*">
                <xsl:if test="name(.) != 'class'">
                    <xsl:copy />
                </xsl:if>
            </xsl:for-each>
            <xsl:value-of select="text()" />
            <xsl:apply-templates select="./*" />
        </h:div>
    </xsl:template>

    <xsl:template name="to-span">
        <xsl:param name="orig" select="." />
        <xsl:param name="orig-class" select="@class" />
        <xsl:param name="add-class" />
        <h:span>
            <xsl:attribute name="class">
                <xsl:if test="@class">
                    <xsl:value-of select="@class" />
                    <xsl:value-of select="' '" />
                </xsl:if>
                <xsl:value-of select="$add-class" />
            </xsl:attribute>
            <xsl:for-each select="@*">
                <xsl:if test="name(.) != 'class'">
                    <xsl:copy />
                </xsl:if>
            </xsl:for-each>
            <xsl:value-of select="text()" />
            <xsl:apply-templates select="./*" />
        </h:span>
    </xsl:template>

    <xsl:template match="h:section | h:article | h:nav | h:header | h:aside | h:hgroup | h:footer | h:address | h:figure | h:figcaption">
        <xsl:call-template name="to-div">
            <xsl:with-param name="add-class" select="concat('html5-', local-name(.))" />
        </xsl:call-template>
    </xsl:template>

    <!-- <xsl:template match="">
        <xsl:call-template name="to-div">
            <xsl:with-param name="add-class" select="concat('html5-', local-name(.))" />
        </xsl:call-template>
    </xsl:template> -->

    <xsl:template match="h:input">
        <input>
            <xsl:choose>
                <xsl:when test="@type = 'email' or @type = 'url' or @type='datetime' or @type='date' or @type='month' or @type='week' or @type='time' or @type='datetime-local' or @type='number' or @type='range' or @type='color' or @type='search'">
                    <xsl:attribute name="type">
                        <xsl:text>text</xsl:text>
                    </xsl:attribute>
                    <xsl:attribute name="class">
                        <xsl:if test="@class">
                            <xsl:value-of select="@class" />
                            <xsl:value-of select="' '" />
                        </xsl:if>
                        <xsl:text>html5-input-</xsl:text>
                        <xsl:value-of select="@type" />
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy select="@type" />
                    <xsl:copy select="@class" />
                </xsl:otherwise>
            </xsl:choose>
            <xsl:for-each select="@*">
                <xsl:if test="name(.) != 'class' and name(.) != 'type'">
                    <xsl:copy />
                </xsl:if>
            </xsl:for-each>
            <xsl:value-of select="." />
            <xsl:apply-templates select="./*" />
        </input>
    </xsl:template>

    <xsl:template match="h:html">
        <h:html>
            <xsl:apply-templates select="./*" />
        </h:html>
    </xsl:template>

</xsl:stylesheet>
