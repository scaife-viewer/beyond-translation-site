import json
from collections import defaultdict
from pathlib import Path

import more_itertools
from lxml import etree


def main():
    path = Path(
        "/Users/jwegner/Data/development/repos/scaife-viewer/scaife-viewer/data/cts/PerseusDL-canonical-greekLit-0.0.4176122695-7070a1d/data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml"
    )

    TEI_NS = {"TEI": "http://www.tei-c.org/ns/1.0"}
    parsed = etree.parse(path)

    version_urn = parsed.xpath("//TEI:div[position()=1]", namespaces=TEI_NS)[
        0
    ].attrib.get("n")
    milestones = parsed.xpath("//TEI:milestone[@unit='card']", namespaces=TEI_NS)
    lookup = defaultdict(list)
    for pos, milestone in enumerate(milestones):
        #  milestone.xpath("./following::TEI:l[position()=1]", namespaces=TEI_NS)[0].attrib
        # milestone.xpath("./ancestor::TEI:div[position()=1]", namespaces=TEI_NS)[0].attrib
        # an alternative here would be to resolve the refsDecls, and then the milestones
        next_line_elem = milestone.xpath(
            "./following::TEI:l[position()=1]", namespaces=TEI_NS
        )[0]
        next_book_elem = next_line_elem.xpath(
            "./ancestor::TEI:div[@type='textpart' and @subtype='Book']",
            namespaces=TEI_NS,
        )[0]
        ref = f'{next_book_elem.attrib["n"]}.{next_line_elem.attrib["n"]}'
        lookup[pos].append(ref)
        try:
            previous_line_elem = milestone.xpath(
                "./preceding::TEI:l[position()=1]", namespaces=TEI_NS
            )[0]
        except IndexError as exception:
            if pos == 0:
                pass
            else:
                raise exception
        else:
            previous_book_elem = previous_line_elem.xpath(
                "./ancestor::TEI:div[@type='textpart' and @subtype='Book']",
                namespaces=TEI_NS,
            )[0]
            ref = f'{previous_book_elem.attrib["n"]}.{previous_line_elem.attrib["n"]}'
            lookup[pos - 1].append(ref)

    # this appends the final line
    last_line_elem = milestone.xpath("./following::TEI:l[last()]", namespaces=TEI_NS)[0]
    last_book_elem = last_line_elem.xpath(
        "./ancestor::TEI:div[@type='textpart' and @subtype='Book']", namespaces=TEI_NS
    )[0]
    last_pos = pos
    ref = f'{last_book_elem.attrib["n"]}.{last_line_elem.attrib["n"]}'
    lookup[pos].append(ref)

    # TODO: Refactor these into book-level TOCs, like we did for folios
    all_tocs = []
    for pos, entry in lookup.items():
        refs = "-".join(entry)
        title = f"lines {refs}"
        if pos == last_pos:
            # this is the last line
            title = f"lines {entry[0]}ff."
        toc = dict(title=title, uri=f"{version_urn}:{refs}")
        all_tocs.append(toc)

    # regroup tocs
    root_items = []
    tocs_by_book = more_itertools.bucket(
        all_tocs, key=lambda x: x["uri"].rsplit(":", maxsplit=1)[1].split(".")[0]
    )
    for book in tocs_by_book:
        urnish = f"toc.iliad-{book}"
        book_entries = tocs_by_book[book]
        root_entry = {
            "title": "↵",
            "uri": "urn:cite:scaife-viewer:toc.iliad",
        }
        data = {
            "@id": f"urn:cite:scaife-viewer:{urnish}",
            "title": f"Book {book}",
            "uri": f"urn:cite:scaife-viewer:{urnish}",
            # TODO: Distinguish between entry title and TOC title
            # "title": f"Folios for Iliad {book}",
            "items": [root_entry] + list(book_entries),
        }
        root_items.append(data)

    iliad_toc_path = Path("data/annotations/tocs/liad-cards/toc.iliad.json")
    data = {
        "@id": "urn:cite:scaife-viewer:toc.iliad",
        "title": "Iliad (Cards)",
        "description": "Mapping of cards to books / lines",
        "items": root_items,
    }
    with iliad_toc_path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
