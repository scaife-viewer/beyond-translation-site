import json
from pathlib import Path

import conllu


# TODO: Djangoify
BASE_DATA_DIR = Path("data")
HILLEARY_DATA_DIR = BASE_DATA_DIR / "raw/ibnsaid"

ENGLISH_VERSION = "urn:cts:arabicLit:amedsaid1831.dw042.perseus-eng1:"


def check_bom(file_path):
    with open(file_path, "rb") as file:
        first_bytes = file.read(3)
    return first_bytes == b"\xef\xbb\xbf"


def load_data(text_path):
    encoding = "utf-8-sig" if check_bom(text_path) else "utf-8"
    return conllu.parse(text_path.read_text(encoding=encoding))


def get_output_path(stem):
    return BASE_DATA_DIR / f"annotations/syntax-trees/{stem}.json"


def extract_references(sentence):
    # assumes scaife_stack_atlas/extractors/process_ibnsaid_trees.py
    # was used to "bake" in references
    return sentence.metadata.get("references", "").split("|")


def extract_syntax_trees(version_urn, path):
    data = load_data(path)

    to_create = []
    version_part = version_urn.rsplit(":", maxsplit=2)[1]
    exemplar = version_part.replace(".", "-")

    for sentence in data:
        sentence_id = int(sentence.metadata["sent_id"])
        sentence_obj = {
            "urn": f"urn:cite2:scaife-viewer:syntaxTree.v1:syntaxTree-{exemplar}-{sentence_id}",
            "treebank_id": sentence_id,
            "words": [],
        }
        for token in sentence:
            head_id = token["head"]
            if head_id is None:
                continue
            word_obj = {
                "id": token["id"],
                "value": token["form"],
                "head_id": token["head"],
                "lemma": token["lemma"],
                "tag": token["upos"],
                "relation": token["deprel"],
            }
            sentence_obj["words"].append(word_obj)

        references = extract_references(sentence)
        sentence_obj.update(
            {
                "references": references,
                "citation": str(sentence_id),
            }
        )
        to_create.append(sentence_obj)

    output_path = get_output_path(version_part)

    json.dump(
        to_create,
        open(output_path, "w"),
        ensure_ascii=False,
        indent=2,
    )


def main():
    version_path_lookup = {
        ENGLISH_VERSION: HILLEARY_DATA_DIR / "amedsaid1831.dw042.perseus-eng1.conllu",
    }
    for version, input_path in version_path_lookup.items():
        extract_syntax_trees(version, input_path)


if __name__ == "__main__":
    main()
