import re
from pathlib import Path
from collections import defaultdict
from lxml import etree

ns = {"TEI": "http://www.tei-c.org/ns/1.0"}


def extract_edition(parsed):
    """
    <citeStructure match="//div[@type='edition']" use="head">
    <citeData property="dc:title" use="head"/>
    <citeData property="function" use="'toc-entry'"/>
    <citeStructure match="p" use="@n" unit="chapter" delim=' '>
        <citeData property="dc:title" use="@n"/>
        <citeData property="dc:identifier" use="@n"/>
        <citeData property="function" use="'toc-entry'"/>
        <citeData property="function" use="'split'"/>
        <citeData property="dc:requires" use="//front/div[@xml:id='bibliography']"/>
        <citeStructure match=".//seg" use="@n" delim="." unit="part"/>
    </citeStructure>
    </citeStructure>
    """
    edition = parsed.find("//TEI:div[@type='edition']", namespaces=ns)
    chapters = edition.findall("TEI:p", namespaces=ns)
    parts = defaultdict(list)
    for chapter in chapters:
        chapter_ref = chapter.attrib["n"]
        parts[chapter_ref] = []
        segments = chapter.findall("TEI:seg", namespaces=ns)
        for segment in segments:
            text_content = []
            segment_ref = segment.attrib["n"]
            text_content.append(segment.text)
            for app in segment.findall("TEI:app", namespaces=ns):
                # TODO: Make use of comments for app crit extraction
                comment = app.getprevious()
                lems = app.findall("TEI:lem", namespaces=ns)
                for lem in lems:
                    # TODO: Process via XSLT?
                    # lem_text = lem.text
                    # if not lem_text:
                    #     lem_text = ""
                    #     for child in lem.iterdescendants():
                    #         try:
                    #             assert child.tag.endswith('supplied') or child.tag.endswith('sic')
                    #         except AssertionError:
                    #             import ipdb ; ipdb.set_trace()
                    #         lem_text += f"<{child.text}>"
                    #         lem_text += child.tail
                    # <ab> incendio
                    # <sic>obiectis</sic>
                    # lem_text = re.sub(r"\s+", " ", lem_text.strip())
                    lem_text = re.sub(r"\s+", " ", lem.xpath("string()").strip())
                    text_content.append(lem_text)
                tail = app.tail
                if tail:
                    text_content.append(tail)
            text_content.append(" ")
            text_content = [s for s in text_content if s]
            text_content = "".join(
                [re.sub(r"\s+", " ", s) for s in text_content if re.sub(r"\s+", " ", s)]
            ).strip()
            parts[chapter_ref].append((segment_ref, text_content))
    return parts


def extract_translation(parsed):
    translation = parsed.find("//TEI:div[@type='edition']", namespaces=ns)
    chapters = translation.findall("TEI:div/[1]/TEI:p", namespaces=ns)
    parts = defaultdict(list)
    for chapter in chapters:
        chapter_ref = chapter.attrib["n"]
        parts[chapter_ref] = []
        segments = chapter.findall("TEI:seg", namespaces=ns)
        for segment in segments:
            text_content = []
            segment_ref = segment.attrib["n"]
            text_content.append(segment.text)
            text_content.append(" ")
            text_content = [s for s in text_content if s]
            text_content = "".join(
                [re.sub(r"\s+", " ", s) for s in text_content if re.sub(r"\s+", " ", s)]
            ).strip()
            parts[chapter_ref].append((segment_ref, text_content))
    return parts


def write_texts(edition_parts, translation_parts):
    # TODO: Verify output by writing simple chapters; just the first each
    edition_path = Path("data/library/phi0428/phi001/phi0428.phi001.dll-ed-lat1.txt")
    with edition_path.open("w") as f:
        for part, children in edition_parts.items():
            output_text = f"{part}. "
            for _, child in children:
                output_text += f"{child} "
            output_text = output_text.strip()
            output_text += "\n"
            f.write(output_text)

    translation_path = Path(
        "data/library/phi0428/phi001/phi0428.phi001.dll-tr-eng1.txt"
    )
    with translation_path.open("w") as f:
        for part, children in translation_parts.items():
            output_text = f"{part}. "
            for _, child in children:
                output_text += f"{child} "
            output_text = output_text.strip()
            output_text += "\n"
            f.write(output_text)


def main():
    path = Path("data/raw/balex/ldlt-balex.xml")
    parsed = etree.parse(path.open("rb"))
    edition_parts = extract_edition(parsed)

    path = Path("data/raw/balex/translation.xml")
    parsed = etree.parse(path.open("rb"))
    translation_parts = extract_translation(parsed)

    write_texts(edition_parts, translation_parts)
