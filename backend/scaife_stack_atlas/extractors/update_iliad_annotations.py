"""
Script used to update the current token annotations to the new format
"""

import csv
from pathlib import Path

from scaife_stack_atlas.postag_convert import deep_morphology_pos_and_parse


def main():
    iliad_annotations_path = Path(
        "data/annotations/token-annotations/iliad-crane-shamsian/tlg0012.tlg001.perseus-grc2.csv"
    )

    updated_rows = []
    annotation_reader = csv.DictReader(
        iliad_annotations_path.open(encoding="utf-8-sig")
    )
    fieldnames = annotation_reader.fieldnames[::]

    assert "case" in fieldnames

    fieldnames.pop(fieldnames.index("case"))
    fieldnames.pop(fieldnames.index("mood"))
    fieldnames.insert(fieldnames.index("tag"), "parse")
    fieldname_set = set(fieldnames)

    for row in annotation_reader:
        new_row = dict()

        for k, v in row.items():
            if k in fieldname_set:
                new_row[k] = v
        pos, parse = deep_morphology_pos_and_parse(new_row["tag"])
        new_row["part_of_speech"] = pos
        new_row["parse"] = parse

        updated_rows.append(new_row)

    with iliad_annotations_path.open("w", encoding="utf-8-sig") as f:
        annotation_writer = csv.DictWriter(f, fieldnames=fieldnames,)
        annotation_writer.writeheader()
        annotation_writer.writerows(updated_rows)


if __name__ == "__main__":
    main()
