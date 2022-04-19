<?xml version="1.0"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:py="urn:python-funcs"
  exclude-result-prefixes="py">

  <xsl:output xml:space="default" method="html"/>

  <xsl:template match="//entryFree">
    <div class="entry">
      <!-- <h2>
        <xsl:value-of select="py:beta_to_uni(./@key)"/>
      </h2> -->
      <xsl:apply-templates/>
    </div>
    <br />
    <br />
  </xsl:template>

  <!-- TODO: Best way to do this? -->
  <xsl:template match="*[@lang = 'greek']">
  <!-- <xsl:template match="orth|foreign|quote"> -->
    <span>
      <xsl:attribute name="class">
        <xsl:value-of select="name(.)" />
        <xsl:value-of select="' '" />
        <xsl:value-of select="./@lang" />
      </xsl:attribute>
      <xsl:value-of select="py:beta_to_uni(./text())"/>
    </span>
  </xsl:template>

  <xsl:template match="bibl">
    <xsl:choose>
      <xsl:when test="starts-with(@n, 'urn')">
        <!-- TODO: Scaife versus other fallback -->
        <a class="bibl">
          <xsl:attribute name="target">
            <xsl:value-of select="'_blank'" />
          </xsl:attribute>
          <xsl:attribute name="data-urn">
            <xsl:value-of select="@n" />
          </xsl:attribute>
          <xsl:attribute name="href">
            <xsl:value-of select="py:catalog_link(.)"/>
          </xsl:attribute>
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <span class="bibl">
          <xsl:apply-templates/>
        </span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tr">
    <span>
      <xsl:attribute name="class">
        <xsl:value-of select="name(.)" />
      </xsl:attribute>
      <xsl:attribute name="style">font-weight: bold;</xsl:attribute>

      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="title">
    <span>
      <xsl:attribute name="class">
        <xsl:value-of select="name(.)" />
      </xsl:attribute>
      <xsl:attribute name="style">font-style: italic;</xsl:attribute>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="author">
    <span>
      <xsl:attribute name="class">
        <xsl:value-of select="name(.)" />
      </xsl:attribute>
      <xsl:attribute name="style">font-variant: small-caps;</xsl:attribute>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- TODO: Move nested senses via UL / LI -->
  <xsl:template match="sense">
    <div style="margin-top: 1.0em;">
      <xsl:attribute name="class">
        <xsl:text>sense </xsl:text>
        <xsl:value-of select="'depth-'" />
        <xsl:value-of select="./@level" />
      </xsl:attribute>
      <span>
        <strong><xsl:value-of select="./@n" />).</strong>
      </span>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- TODO: Improve whitespace formatting -->
  <!-- <xsl:strip-space elements="*" /> -->
</xsl:stylesheet>
