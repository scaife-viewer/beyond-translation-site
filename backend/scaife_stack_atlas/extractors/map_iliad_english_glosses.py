import csv
from pathlib import Path

from scaife_viewer.atlas.language_utils import normalize_string


def build_eng_glosses_lookup():
    eng_glosses_path = Path("data/raw/homer-dik/shortdefsGreekEnglishLogeion.tsv")
    gloss_lu = {}
    gloss_reader = iter(
        csv.DictReader(eng_glosses_path.open(encoding="utf-8-sig"), delimiter="\t")
    )
    for row in gloss_reader:
        # lemma = normalize_string(row["lemma"])
        # # Store the normalized lemma form
        # gloss_lu[lemma] = row["def"]

        # Store the exact lemma form
        gloss_lu[row["lemma"]] = row["def"]
    return gloss_lu


def main():
    iliad_annotations_path = Path(
        "data/annotations/token-annotations/iliad-crane-shamsian/tlg0012.tlg001.perseus-grc2.csv"
    )

    gloss_lu = build_eng_glosses_lookup()
    updated_rows = []
    annotation_reader = csv.DictReader(
        iliad_annotations_path.open(encoding="utf-8-sig")
    )
    for row in annotation_reader:
        # # lookup using the normalized lemma form
        # row["gloss (eng)"] = gloss_lu.get(normalize_string(row["lemma"]), "")
        # lookup using the exact lemma form
        gloss = gloss_lu.get(row["lemma"], None)
        if not gloss:
            # TODO: Work with @jtauber to determine a valid fallback path
            gloss = gloss_lu.get(normalize_string(row["lemma"]), "")
        row["gloss (eng)"] = gloss
        updated_rows.append(row)

    with iliad_annotations_path.open("w", encoding="utf-8-sig") as f:
        annotation_writer = csv.DictWriter(
            f,
            fieldnames=updated_rows[0].keys(),
        )
        annotation_writer.writeheader()
        annotation_writer.writerows(updated_rows)


if __name__ == "__main__":
    main()
