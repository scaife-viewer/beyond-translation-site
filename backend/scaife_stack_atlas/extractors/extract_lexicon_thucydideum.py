import itertools
import json
from functools import lru_cache
from pathlib import Path

import jsonlines
from lxml import etree
from more_itertools import peekable


CATALOG_API_HOST = "catalog-api-dev.scaife.eldarion.com"

DICTIONARY_PATH = Path("data/annotations/dictionaries/lexicon-thucydideum")
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XSL_STYLESHEET_PATH = Path("data/raw/lexicon-thucydideum/lexicon-thucydideum.xsl")


class XSLTransformer:
    def __init__(self, xml):
        self.xml = xml

    def canonical_urn_link(self, ctx, value):
        node = value[0]
        urn = node.attrib["urn"]
        return f"https://{CATALOG_API_HOST}/{urn}/canonical-url/"

    # TODO: Backported from scaife_viewer_core TEIRenderer
    @lru_cache
    def render(self):
        with XSL_STYLESHEET_PATH.open("rb") as f:
            func_ns = "urn:python-funcs"
            transform = etree.XSLT(
                etree.XML(f.read()),
                extensions={
                    (func_ns, "canonical_urn_link"): self.canonical_urn_link,
                },
            )
            try:
                return str(transform(self.xml))
            except Exception:
                for error in transform.error_log:
                    print(error.message, error.line)
                raise


def clean_xml_namespaces(root):
    for element in root.getiterator():
        if isinstance(element, etree._Comment):
            continue
        element.tag = etree.QName(element).localname
    etree.cleanup_namespaces(root)


def convert_to_urns(root):
    for element in root.getiterator():
        if element.tag == "bibl":
            # <bibl n="thuc. 7.65.2">
            value = element.attrib["n"]
            ref = value.split("thuc. ").pop()
            urn = f"urn:cts:greekLit:tlg0003.tlg001.perseus-grc2:{ref}"
            element.attrib["urn"] = urn


def extract_entries():
    counters = dict(
        sense=0,
        entry=0,
        citation=0,
    )
    # NOTE: obtained from https://github.com/gregorycrane/Thucydides-new-working-materials/blob/e9d159202e4498d7ec55144d7d082108f2e8c40a/betant.thuclex_lateng.xml
    path = Path("data/raw/lexicon-thucydideum/betant.thuclex_lateng.xml")
    parsed = etree.parse(path.open())
    entries = parsed.xpath(
        '//tei:div[@type="textpart" and @subtype="entry"]', namespaces=TEI_NS
    )
    for entry in entries:
        counters["entry"] += 1
        key = counters["entry"]
        headword = " ".join(
            entry.xpath("./tei:head/tei:foreign/text()", namespaces=TEI_NS)
        )
        display = f"<b>{headword}</b>"
        clean_xml_namespaces(entry)
        convert_to_urns(entry)
        transformer = XSLTransformer(entry)
        content = (
            transformer.render()
            .strip()
            .replace('xmlns="http://www.tei-c.org/ns/1.0"', "")
        )
        content = f'<div class="entry">{content}</div>'
        yield dict(
            headword=headword,
            data=dict(headword_display=display, content=content, key=key),
            senses=[],
            citations=[],
            urn=f"urn:cite2:scafife-viewer:dictionary-entries.atlas_v1:lexicon-thucydideum-{counters['entry']}",
        )


def blob_entries():
    counter = 1
    entries = extract_entries()
    CHUNK_SIZE = 10000
    chunk = peekable(itertools.islice(entries, CHUNK_SIZE))
    entry_paths = []
    while chunk:
        entries_path = Path(DICTIONARY_PATH, f"entries-{str(counter).zfill(3)}.jsonl")
        print(counter)
        with entries_path.open("w") as f:
            writer = jsonlines.Writer(f)
            for entry in chunk:
                writer.write(entry)
        entry_paths.append(entries_path.name)
        counter += 1
        chunk = peekable(itertools.islice(entries, CHUNK_SIZE))
        if not chunk:
            break

    data = {
        "label": "Lexicon Thucydideum",
        "urn": "urn:cite2:scaife-viewer:dictionaries.v1:lexicon-thucydideum",
        "kind": "Dictionary",
        "entries": entry_paths,
    }
    metadata_path = Path(DICTIONARY_PATH, "metadata.json")
    with metadata_path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    DICTIONARY_PATH.mkdir(exist_ok=True, parents=True)
    blob_entries()


if __name__ == "__main__":
    main()
