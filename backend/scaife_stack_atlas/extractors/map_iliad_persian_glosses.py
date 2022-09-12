import csv
from pathlib import Path


def main():
    persian_glosses_path = Path("data/raw/homer-farnoosh/persian_iliad1_glosses.csv")
    gloss_lu = {}
    gloss_reader = iter(csv.reader(persian_glosses_path.open()))
    for row in gloss_reader:
        gloss_lu[row[1]] = row[3]

    paths = [
        Path(
            "data/annotations/token-annotations/iliad-crane-shamsian/tlg0012.tlg001.perseus-grc2.csv"
        ),
        Path(
            "data/annotations/token-annotations/od-crane/tlg0012.tlg002.perseus-grc2.csv"
        ),
    ]

    for annotation_path in paths:
        updated_rows = []
        annotation_reader = csv.DictReader(annotation_path.open(encoding="utf-8-sig"))
        for row in annotation_reader:
            gloss = gloss_lu.get(row["lemma"], "")
            row["gloss (fas)"] = gloss
            updated_rows.append(row)

        fieldnames = [
            "ve_ref",
            "value",
            "word_value",
            "lemma",
            "part_of_speech",
            "gloss (eng)",
            "gloss (fas)",
            "parse",
            "tag",
        ]
        annotation_writer = csv.DictWriter(
            annotation_path.open("w", encoding="utf-8-sig"),
            fieldnames=fieldnames,
        )
        annotation_writer.writeheader()
        annotation_writer.writerows(updated_rows)


if __name__ == "__main__":
    main()
