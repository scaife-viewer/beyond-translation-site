import json
from lxml import etree
from pathlib import Path
from collections import defaultdict


def main():
    path = Path(
        "/Users/jwegner/Data/development/repos/scaife-viewer/scaife-viewer/data/cts/PerseusDL-canonical-greekLit-0.0.4176122695-7070a1d/data/tlg0011/tlg002/tlg0011.tlg002.perseus-grc2.xml"
    )

    TEI_NS = {"TEI": "http://www.tei-c.org/ns/1.0"}
    parsed = etree.parse(path)

    version_urn = parsed.xpath("//TEI:div[position()=1]", namespaces=TEI_NS)[
        0
    ].attrib.get("n")
    milestones = parsed.xpath("//TEI:milestone", namespaces=TEI_NS)
    lookup = defaultdict(list)
    for pos, milestone in enumerate(milestones):
        #  milestone.xpath("./following::TEI:l[position()=1]", namespaces=TEI_NS)[0].attrib
        # milestone.xpath("./ancestor::TEI:div[position()=1]", namespaces=TEI_NS)[0].attrib
        # an alternative here would be to resolve the refsDecls, and then the milestones
        next_line = milestone.xpath(
            "./following::TEI:l[position()=1]", namespaces=TEI_NS
        )[0].attrib.get("n")
        lookup[pos].append(next_line)
        try:
            previous_line = milestone.xpath(
                "./preceding::TEI:l[position()=1]", namespaces=TEI_NS
            )[0].attrib.get("n")
        except IndexError as exception:
            if pos == 0:
                pass
            else:
                raise exception
        else:
            lookup[pos - 1].append(previous_line)
    # this appends the final line
    last_line = milestone.xpath("./following::TEI:l[last()]", namespaces=TEI_NS)[
        0
    ].attrib.get("n")
    last_pos = pos
    lookup[pos].append(last_line)

    tocs = []
    for pos, entry in lookup.items():
        refs = "-".join(entry)
        title = f"lines {refs}"
        if pos == last_pos:
            # this is the last line
            title = f"lines {entry[0]}ff."
        toc = dict(title=title, uri=f"{version_urn}:{refs}")
        tocs.append(toc)

    antigone_toc_path = Path("data/tocs/toc.antigone.json")
    data = {
        "@id": "urn:cite:scaife-viewer:toc.antigone",
        "title": "Antigone (Cards)",
        "description": "Mapping of cards to lines",
        "items": tocs,
    }
    with antigone_toc_path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
