import json
import re
from pathlib import Path

from lxml import etree


EXTRACTOR_PATTERN = re.compile(r"(?P<version>\w{2}\.)\s(?P<ref>.*)")
VERSION_ALIAS_LOOKUP = {
    "Il.": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
    "Od.": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:",
}
CITATION_TAG = "{http://www.tei-c.org/ns/1.0}cit"
TEI_NS = {"TEI": "http://www.tei-c.org/ns/1.0"}
ENTRY_URN_PREFIX = "urn:cite2:exploreHomer:entries.atlas_v1:2."


def ref_to_urn(ref):
    if not ref:
        return
    match = EXTRACTOR_PATTERN.match(ref)
    if not match:
        return
    alias, ref = match.groups()
    return f"{VERSION_ALIAS_LOOKUP[alias]}{ref}"


def extract_citations(sense_urn, sense):
    citation_urn_part = sense_urn.rsplit(":")[-1]
    base_urn = f"urn:cite2:scholarlyEditions:citations.v1:{citation_urn_part}"
    citations = []
    cite_idx = 0
    for bibl in sense.iterfind("{http://www.tei-c.org/ns/1.0}bibl", namespaces=TEI_NS):
        ref = bibl.attrib["n"].split("Hom. ").pop()
        citations.append(
            {
                "urn": f"{base_urn}_{cite_idx}",
                "data": {
                    "ref": ref,
                    "urn": ref_to_urn(ref),
                    "quote": etree.tostring(bibl, method="text", encoding="utf-8")
                    .decode("utf-8")
                    .strip(),
                },
            }
        )
        cite_idx += 1
    return citations


def main():
    path = Path("data/raw/cunliffe/cunliffe.hompers.unicode.xml")
    with path.open() as f:
        tree = etree.parse(f)
        sense_idx = 1
        entries = []
        path = "//{http://www.tei-c.org/ns/1.0}div[@n]"
        # TODO: Determine if we need a tweaked selector to handle nested senes
        for entry in tree.iterfind(path, namespaces=TEI_NS):
            head_el = entry.find("{http://www.tei-c.org/ns/1.0}head", namespaces=TEI_NS)

            if head_el is None:
                continue

            head_text = (
                etree.tostring(head_el, method="text", encoding="utf-8")
                .decode("utf-8")
                .strip()
            )

            slug = entry.attrib["{http://www.w3.org/XML/1998/namespace}id"].split(
                "-cunliffe-name"
            )[0]
            label_parts = slug.split("-")
            label_parts = [p.title() for p in label_parts]
            label = " ".join(label_parts)
            senses = []
            for sense in entry.iterfind(
                "{http://www.tei-c.org/ns/1.0}p", namespaces=TEI_NS
            ):
                definition = (
                    etree.tostring(sense, method="text", encoding="utf-8")
                    .decode("utf-8")
                    .strip()
                )
                sense_urn = f"urn:cite2:exploreHomer:senses.atlas_v1:2.{sense_idx}"
                citations = extract_citations(sense_urn, sense)
                if citations:
                    first_citation = citations[0]["data"]["quote"]
                    definition = definition.split(first_citation)[0]
                senses.append(
                    {
                        "idx": sense_idx,
                        "label": "",
                        "definition": definition,
                        "citations": citations,
                        "urn": sense_urn,
                    }
                )
                sense_idx += 1

            entries.append(
                {
                    "headword": head_text,
                    "senses": senses,
                    "data": {"content": label,},
                    "urn": f"{ENTRY_URN_PREFIX}{sense_idx}",
                }
            )
            sense_idx += 1

        data = {
            "label": "Cunliffe (Hompers)",
            "urn": "urn:cite2:scaife-viewer:dictionaries.v1:cunliffe-hompers",
            "kind": "Dictionary",
            "entries": entries,
        }
        output_path = Path("data/annotations/dictionaries/cunliffe-2-hompers.json")
        with output_path.open("w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
