import csv
import logging
import re
from collections import defaultdict
from pathlib import Path

import jsonlines
from lxml import html


OUTPUT_DIR = Path("data/annotations/grammatical-entries/didakta")
PUNCTUATION_ONLY_WORD_VALUES = set([";", ".", ",", "·"])

logger = logging.getLogger(__name__)


def extract_grammatical_entries():
    path = Path("data/raw/didakta/DidaktaGrammarforAnnotation.html")
    parsed = html.parse(path.open("rb"))

    entry_lookup = dict()
    for elem in parsed.xpath(f"//a[starts-with(text(), '§')]"):
        title = elem.text.strip("§")
        if title:
            entry_lookup[title] = elem.attrib["href"][1:]

    entries = []
    idx = 0
    for entry_title in entry_lookup.keys():
        entry_id = entry_lookup[entry_title]
        entry_headword = entry_title.split()[0]
        heading = next(
            iter(parsed.xpath(f"//h3[@id='{entry_id}']")),
            None,
        )
        if heading is None:
            logger.warning("Could not resolve an entry for {entry_headword}")
            continue

        parts = [
            # NOTE: We're excluding the heading
            # as it duplicates the `title` field
            # heading
        ]
        for elem in heading.itersiblings():
            if elem.tag == "h3":
                break
            parts.append(elem)

        body = html.Element("div")
        body.extend(parts)
        for elem in body.iterdescendants():
            # NOTE: Strip inline styles
            elem.attrib.pop("style", None)
            elem.attrib.pop("name", None)
            elem.attrib.pop("class", None)

        # Remove "Middle Voice" headings
        h1_elems = body.xpath("//h1")
        if len(h1_elems):
            for elem in h1_elems:
                parent = elem.getparent()
                parent.remove(elem)

        # Remove empty "a" tags
        anchor_elems = body.xpath("//a")
        if len(anchor_elems):
            for elem in anchor_elems:
                if not elem.attrib.get("href"):
                    elem.tag = "span"

        body_content = html.tostring(body, encoding="unicode")
        body_content = re.sub(r"\s+", " ", body_content)
        entries.append(
            dict(
                label=entry_headword,
                data=dict(
                    title=entry_title,
                    description=body_content,
                ),
                idx=idx,
                urn=f"urn:cite2:scafife-viewer:grammatical-entries.atlas_v1:didakta-{idx + 1}",
            )
        )
        idx += 1
        # FIXME: Preferred sort?
        # We're using thematic on the frontend
        # but alphanumeric here.
        # If we brought in "Middle Voice", etc into our
        # data model that could help
    return entries


def write_entries(entries):
    entries_path = OUTPUT_DIR / "entries.jsonl"
    # TODO: Revisit 1,000 entry chunking as we had for
    # LSJ extraction
    with entries_path.open("w") as f:
        writer = jsonlines.Writer(f)
        for row in entries:
            writer.write(row)


def cleaned_tags(value):
    cleaned = []
    tags = [t.strip() for t in value.split("|")]
    for tag in tags:
        for subtag in tag.split():
            if subtag.endswith("."):
                cleaned.append(subtag)
            elif subtag == "GBP":
                # GBP in spreadsheet,
                # GBP. in Didakta
                cleaned.append("GBP.")
    return cleaned


def extract_tokens():
    # Import token annotations
    token_count = 0
    lu_path = Path(
        "data/annotations/token-annotations/iliad-crane-shamsian/tlg0012.tlg001.perseus-grc2.csv"
    )
    reader = csv.DictReader(lu_path.open(encoding="utf-8-sig"))
    # Build up tokens by ve refs
    ve_ref_by_ref = defaultdict(list)
    for row in reader:
        ref = row["ve_ref"].split(".t")[0]
        tref = row["ve_ref"].split(f"{ref}.")[1]
        ve_ref_by_ref[ref].append((tref, row["value"]))
        token_count += 1

    # FIXME: Data bug where we've duplicated a row
    ve_ref_by_ref["1.220"].pop(1)

    # Load annotations from Google Sheet
    path = Path(
        "data/raw/didakta/google_sheets_165AyncuQRUrjfDGB-2yI3dKS9UwDBgF-421Z6f5fpE4_ws_Sheet1.csv"
    )
    tokens_by_ref_lookup = defaultdict(list)
    reader = csv.DictReader(path.open())
    token_count = 0
    for row in reader:
        col10 = row["Column 10"]
        if not col10:
            continue
        ref = col10.strip("Ref=").split("|")[0]
        if ref == "_":
            continue

        word_value = row["Column 2"].strip()
        if word_value in PUNCTUATION_ONLY_WORD_VALUES:
            continue

        tokens_by_ref_lookup[ref].append(
            dict(value=word_value, didakta_tags=cleaned_tags(row["MG tags"]))
        )
        token_count += 1

    to_fix = []
    has_differences = 0
    for key, values in tokens_by_ref_lookup.items():
        canonical_values = ve_ref_by_ref[key]
        this_count = len(values)
        that_count = len(canonical_values)
        if this_count != that_count:
            has_differences += 1
            to_fix.append((key, canonical_values, values))

    # 39 lines with differences
    fixed = []
    for key, canonical_values, values in to_fix:
        new_values = []
        for tref, value in canonical_values:
            match = next(iter(filter(lambda x: x["value"] == value, values)), None)
            if match:
                new_values.append(match)
        if len(new_values) != len(canonical_values):
            logger.warning(key)
            continue
        fixed.append((key, canonical_values, new_values))

    # Now that the lines are fixed, write out to ve_refs
    for key, _, values in fixed:
        tokens_by_ref_lookup[key] = values

    # FIXME: Lemmas work better here?
    csv_path = OUTPUT_DIR / "tokens.csv"
    with csv_path.open("w") as f:
        # FIXME: Value vs Word Value vs Sub Ref value
        # FIXME: Support additional versions
        writer = csv.DictWriter(f, fieldnames=["ve_ref", "value", "tags"])
        writer.writeheader()
        for ref, values in tokens_by_ref_lookup.items():
            canonical_values = ve_ref_by_ref[ref]
            for cval, val in zip(canonical_values, values):
                if val["value"] != cval[1]:
                    # should come down to normalization issues
                    debug_data = "\t".join([ref, cval[0], cval[1], val["value"]])
                    msg = f"Canonical / Didakta value difference: {debug_data}"
                    logger.warning(msg)
                writer.writerow(
                    dict(
                        ve_ref=f"{ref}.{cval[0]}",
                        value=val["value"],
                        tags=";".join(val["didakta_tags"]),
                    )
                )


def main():
    entries = extract_grammatical_entries()
    write_entries(entries)

    extract_tokens()


if __name__ == "__main__":
    main()
