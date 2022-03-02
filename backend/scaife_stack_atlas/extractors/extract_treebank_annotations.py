"""
Script used to extract Odyssey treebank annotations
"""
from collections import Counter
import csv
from pathlib import Path

from scaife_stack_atlas.postag_convert import deep_morphology_pos_and_parse


def main():
    input_path = Path(
        "/Users/jwegner/Data/development/repos/gregorycrane/Homerica/tlg0012-tbankplus.txt"
    )
    odyssey_annotations_path = Path(
        "data/annotations/token-annotations/od-crane/tlg0012.tlg002.perseus-grc2.csv"
    )

    fieldnames = [
        "ve_ref",
        "value",
        "word_value",
        "lemma",
        "part_of_speech",
        "parse",
        "tag"
    ]
    annotations = []
    refcounter = Counter()
    with input_path.open() as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            try:
                _, urn, tree_id, lemma, form, postag, _, _, _ = row
            except:
                print(row)
                continue

            if row[0].startswith("#"):
                continue

            if not urn.startswith("urn:cts:greekLit:tlg0012.tlg002"):
                continue
            annotation = dict()
            ref, subref = urn.rsplit(":", maxsplit=1)[1].split("@")
            try:
                book, line = ref.split(".")
            except:
                # TODO: fix these
                print(urn)
                continue
            refcounter[ref] += 1
            position = refcounter[ref]
            annotation["ve_ref"] = f"{book}.{line}.t{position}"
            # YAGNI
            # annotation["value"] = ""
            # annotation["word_value"] = ""
            annotation["lemma"] = lemma
            annotation["tag"] = postag
            annotation["pos"], annotation["parse"] = deep_morphology_pos_and_parse(postag)
            annotations.append(annotation)

    with odyssey_annotations_path.open("w", encoding="utf-8-sig") as f:
        annotation_writer = csv.DictWriter(f, fieldnames=fieldnames,)
        annotation_writer.writeheader()
        annotation_writer.writerows(annotations)


if __name__ == "__main__":
    main()
