import json
from pathlib import Path

from betacode.conv import beta_to_uni
from lxml import etree


def get_elements(root, nattr=None):
    if nattr:
        return root.xpath(f"//entryFree[@id='{nattr}']")
    return root.xpath("//entryFree")


def to_unicode(element):
    if element.attrib.get("lang") == "greek":
        element.text = beta_to_uni(element.text)


def stringish(element):
    text = (
        etree.tostring(element, with_tail=True, encoding="utf-8", method="text")
        .decode("utf-8")
        .strip()
    )
    # TODO: Revisit excessive whitepace stripping; was a problem on Cunliffe and likely an issue here too
    return " ".join(s.strip() for s in text.split() if s.strip())


def healed_citation_urn(urnish):
    # FIXME: This should be done / handled within the app at runtime; shortcut
    # for a demo
    if not urnish:
        return ""
    if not urnish.count("tlg0012"):
        return ""
    urnish = urnish.replace("perseus-grc1", "perseus-grc2")
    # TODO: Validate this in case we have other forms of URNs
    version, ref = urnish.rsplit(":", maxsplit=1)
    return f"{version}.{ref}"


def process_citation(c_element, counters):
    # TODO: multiple quotes
    assert c_element.findall("quote")
    assert c_element.findall("bibl")
    quote_parts = []
    for q_elem in c_element.findall("quote"):
        to_unicode(q_elem)
        quote_parts.append(
            etree.tostring(q_elem, with_tail=True, encoding="utf-8", method="text")
            .decode("utf-8")
            .strip()
        )

    quote = " ".join(quote_parts).strip()
    bibl_entries = []
    for b_element in c_element.findall("bibl"):
        # TODO: get creative with XSL or other transforms
        urnish = healed_citation_urn(b_element.attrib.get("n", ""))
        bibl_entries.append((stringish(b_element), urnish))
    assert len(bibl_entries) == 1

    counters["citation"] += 1
    return dict(
        urn=f"urn:cite2:scaife-viewer:citations.atlas_v1:lsj-{counters['citation']}",
        data=dict(quote=quote, ref=bibl_entries[0][0], urn=urnish),
    )


def process_sense(s_element, counters):
    label = s_element.attrib.get("n", "")
    definition = []
    citations = []

    for pos, child in enumerate(s_element.getchildren()):
        if child.tag in ["orth", "gen", "bibl"]:
            to_unicode(child)
            # TODO: review whitespace here; gets a little tricky
            definition.append(stringish(child))
        if child.tag == "cit":
            citations.append(process_citation(child, counters))

    counters["sense"] += 1
    return dict(
        label=label,
        urn=f"urn:cite2:scaife-viewer:senses.atlas_v1:lsj-{counters['sense']}",
        definition=" ".join(definition),
        citations=citations,
    )


def verbose_append(iterable, element):
    iterable.append(element)
    # print(element)


def get_entries():
    paths_and_nattrs = [
        (
            # ἀείδω
            Path("data/raw/lsj/grc.lsj.perseus-eng1.xml"),
            "n1587",
        ),
        (
            # μῆνις
            Path("data/raw/lsj/grc.lsj.perseus-eng13.xml"),
            "n67485",
        ),
    ]
    entries = []
    counters = dict(sense=0, entry=0, citation=0,)
    for path, nattr in paths_and_nattrs:
        root = etree.parse(path.open("rb"))
        elements = get_elements(root, nattr)
        processed = []
        senses = []
        for entry in elements:
            for pos, child in enumerate(entry.getchildren()):
                print(pos, child.tag)
                if child.attrib.get("lang") == "greek":
                    to_unicode(child)
                    verbose_append(processed, stringish(child))
                elif child.tag == "gramGrp":
                    for gchild in child.getchildren():
                        verbose_append(processed, stringish(gchild))
                    if child.tail:
                        verbose_append(processed, child.tail.strip())
                elif child.tag == "sense":
                    sense = child
                    senses.append(process_sense(sense, counters))
                else:
                    verbose_append(processed, stringish(child))
        plain_content = " ".join(processed)
        headword = beta_to_uni(entry.attrib.get("key"))

        counters["entry"] += 1
        entries.append(
            dict(
                headword=headword,
                data=dict(content=f"<p>{plain_content}</p>"),
                senses=senses,
                urn=f"urn:cite2:scafife-viewer:dictionary-entries.atlas_v1:lsj-{counters['entry']}",
            )
        )
    return entries


def main():
    entries = get_entries()

    data = {
        "label": "A Greek-English Lexicon (LSJ)",
        "urn": "urn:cite2:scaife-viewer:dictionaries.v1:lsj",
        "kind": "Dictionary",
        "entries": entries,
    }
    output_path = Path("data/annotations/dictionaries/lsj-sample.json")
    with output_path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
