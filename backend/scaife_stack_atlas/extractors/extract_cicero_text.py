import re
from pathlib import Path

from lxml import etree


DATA_DIR = Path("data")
TEI_NS = {"TEI": "http://www.tei-c.org/ns/1.0"}


def generate_ref(ref_parts):
    return ".".join(ref_parts.values())


def extract_textparts(input_path):
    textparts = []
    with input_path.open() as f:
        tree = etree.parse(f)
    for book in tree.xpath(f"//TEI:div[@subtype='Book']", namespaces=TEI_NS):
        ref_parts = {
            "book": book.attrib["n"],
            "letter": "0",
            "section": "0",
        }
        text = book.find("TEI:head", namespaces=TEI_NS).text.strip()

        # NOTE: We are textparts at chapter.letter.section
        # because SV 2 currently only attaches tokens at the lowest citable
        # node
        textparts.append((generate_ref(ref_parts), text,))

        for letter in book.findall(f"TEI:div[@subtype='letter']", namespaces=TEI_NS):
            ref_parts["letter"] = letter.attrib["n"]

            label = letter.find("TEI:label", namespaces=TEI_NS)
            for pos, child in enumerate(label.iterchildren()):
                ref_parts["section"] = f"{child.xpath('local-name()')}-{pos}"
                text = re.sub(r"\s+", " ", child.xpath("string()")).strip()

                # NOTE: We are textparts at chapter.letter.section
                # because SV 2 currently only attaches tokens at the lowest citable
                # node.
                textparts.append((generate_ref(ref_parts), text,))

            for section in letter.findall(
                f"TEI:div[@subtype='section']", namespaces=TEI_NS
            ):
                ref_parts["section"] = section.attrib["n"]
                text = re.sub(r"\s+", " ", section.xpath("string()").strip())

                textparts.append((generate_ref(ref_parts), text,))
    return textparts


def get_file_path(version_urn):
    workpart_part = version_urn.rsplit(":", maxsplit=2)[1]
    parts = workpart_part.split(".")[0:-1]
    work_dir = Path("data/library", *parts)
    work_dir.mkdir(exist_ok=True, parents=True)
    return Path(work_dir, f"{workpart_part}.txt")


def write_text_file(output_path, textparts):
    with output_path.open("w") as f:
        for part in textparts:
            print(" ".join(part), file=f)


def main():
    input_path = Path(
        DATA_DIR, "raw/cicero-feeney-nadel/phi0474.phi056.perseus-lat1.xml"
    )
    textparts = extract_textparts(input_path)

    version_urn = "urn:cts:latinLit:phi0474.phi056.perseus-lat1-text:"
    output_path = get_file_path(version_urn)
    write_text_file(output_path, textparts)


if __name__ == "__main__":
    main()
