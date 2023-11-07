<?xml version="1.0"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:py="urn:python-funcs"
  exclude-result-prefixes="py">

  <xsl:output xml:space="default" method="html"/>

  <xsl:template match="head">
  </xsl:template>

  <xsl:template match="hi">
    <span>
      <xsl:attribute name="class">
        <xsl:value-of select="name(.)" />
      </xsl:attribute>
      <xsl:attribute name="style">font-style: italic;</xsl:attribute>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="p">
    <p>
      <xsl:attribute name="style">display: block; margin: 1em 0;</xsl:attribute>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="gloss">
    <span>
      <xsl:attribute name="class">
        <xsl:value-of select="name(.)" />
      </xsl:attribute>
      <xsl:attribute name="style">font-style: italic;</xsl:attribute>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="bibl">
    <xsl:choose>
      <xsl:when test="@urn">
        <!-- TODO: Scaife versus other fallback -->
        <a class="bibl">
          <xsl:attribute name="target">
            <xsl:value-of select="'_blank'" />
          </xsl:attribute>
          <xsl:attribute name="data-urn">
            <xsl:value-of select="@n" />
          </xsl:attribute>
          <xsl:attribute name="href">
            <xsl:value-of select="py:canonical_urn_link(.)"/>
          </xsl:attribute>
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:otherwise>
          <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

<xsl:template match="@*|node()">
   <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
   </xsl:copy>
</xsl:template>

</xsl:stylesheet>
