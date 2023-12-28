import json
from pathlib import Path

import conllu


GIO_DATA_DIR = Path(
    "/Users/jwegner/Data/development/repos/gregorycrane/gio-perseus-work-summer-2023"
)
# TODO: Djangoify
BASE_DATA_DIR = Path("data")

GREEK_VERSION = "urn:cts:greekLit:tlg2022.tlg007.gio-grc1:"
ENGLISH_VERSION = "urn:cts:greekLit:tlg2022.tlg007.gio-eng1:"


def check_bom(file_path):
    with open(file_path, "rb") as file:
        first_bytes = file.read(3)
    return first_bytes == b"\xef\xbb\xbf"


def load_data(text_path):
    encoding = "utf-8-sig" if check_bom(text_path) else "utf-8"
    return conllu.parse(text_path.read_text(encoding=encoding))


def get_output_path(stem):
    return BASE_DATA_DIR / f"annotations/syntax-trees/{stem}.json"


def get_scaife_id(version_urn, sentence_id):
    # our IDs are 1-indexed, but Gio's data is 0-indexed
    scaife_id = sentence_id + 1
    if version_urn == ENGLISH_VERSION:
        if sentence_id >= 61:
            scaife_id = sentence_id
        if sentence_id >= 79:
            scaife_id = sentence_id - 1
        return scaife_id
    if sentence_id <= 5:
        return scaife_id

    overrides = {
        1500: 7,
        1501: 8,
        1502: 9,
        1600: 71,
    }
    if sentence_id in overrides:
        return overrides[sentence_id]

    if sentence_id >= 7:
        scaife_id = sentence_id + 3

    if sentence_id >= 35:
        scaife_id = sentence_id + 2

    if sentence_id >= 38:
        scaife_id = sentence_id + 1

    if sentence_id >= 70:
        scaife_id = sentence_id + 2

    if sentence_id >= 70:
        scaife_id = sentence_id + 2

    if sentence_id >= 77:
        scaife_id = sentence_id - 1

    if sentence_id >= 124:
        scaife_id = sentence_id - 2

    return scaife_id


def extract_syntax_trees(version_urn, path):
    data = load_data(path)

    to_create = []
    version_part = version_urn.rsplit(":", maxsplit=2)[1]
    exemplar = version_part.replace(".", "-")

    for sentence in data:
        sentence_id = int(sentence.metadata["sent_id"])
        scaife_id = get_scaife_id(version_urn, sentence_id)

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

        # TODO: can't do cite or refs just yet, which will be required
        # This is likely something we could do from that sent_id as another
        # kind of lookup
        references = [f"{version_urn}{scaife_id}"]
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
        GREEK_VERSION: GIO_DATA_DIR / "Grc_UD_Corr.conllx",
        ENGLISH_VERSION: GIO_DATA_DIR / "Or 27_Eng_UD_Corr.conllx",
    }
    for version, input_path in version_path_lookup.items():
        extract_syntax_trees(version, input_path)


if __name__ == "__main__":
    main()

# remaining steps
# - [] attribution records
