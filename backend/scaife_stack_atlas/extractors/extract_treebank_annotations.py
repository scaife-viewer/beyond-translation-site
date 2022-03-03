"""
Script used to extract Odyssey treebank annotations
"""
from collections import Counter
import json
from pathlib import Path

from scaife_viewer.atlas import tokenizers
from scaife_stack_atlas.postag_convert import deep_morphology_pos_and_parse


def main():
    input_path = Path(
        "data/annotations/syntax-trees/gregorycrane_gagdt_syntax_trees_tlg0012.tlg002.perseus-grc2.json"
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
        "tag",
    ]
    annotations = []
    refcounter = Counter()
    with input_path.open() as f:
        data = json.load(f)
        for row in data:
            for word in row["words"]:
                annotation = dict()
                try:
                    ref = word["ref"]
                except KeyError:
                    print(word)
                    continue
                try:
                    book, line = ref.split(".")
                except ValueError:
                    print(ref)
                    continue

                word_value = tokenizers.Token.get_word_value(word["value"])
                if not word_value:
                    continue

                refcounter[ref] += 1
                position = refcounter[ref]
                annotation["ve_ref"] = f"{book}.{line}.t{position}"
                annotation["word_value"] = word_value
                annotation["value"] = word["value"]
                annotation["lemma"] = word["lemma"]
                annotation["tag"] = word["tag"]
                (
                    annotation["part_of_speech"],
                    annotation["parse"],
                ) = deep_morphology_pos_and_parse(word["tag"])
                annotations.append(annotation)

    with odyssey_annotations_path.open("w", encoding="utf-8-sig") as f:
        annotation_writer = csv.DictWriter(f, fieldnames=fieldnames,)
        annotation_writer.writeheader()
        annotation_writer.writerows(annotations)


if __name__ == "__main__":
    main()
