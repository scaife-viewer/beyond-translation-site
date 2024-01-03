# from https://github.com/scaife-viewer/ogl-pdl-annotations/blob/feature/dictionaries/pipelines/syntax_trees/ud.py
import json
import sys
from pathlib import Path

import conllu


def get_output_path(input_path):
    base_dir = Path(f"data/annotations/syntax-trees")
    base_dir.mkdir(parents=True, exist_ok=True)
    return Path(base_dir, f"{input_path.stem}.json")


def main():
    input_path = Path(sys.argv[1])
    version_urn = sys.argv[2]
    version_part = version_urn.rsplit(":", maxsplit=2)[1]
    exemplar = version_part.replace(".", "-")
    # versionish_urn = f"{str(version_urn)[:-1]}-trees:"
    versionish_urn = f"{str(version_urn)[:-1]}-daphne-trees:"

    data = conllu.parse(input_path.read_text())
    meta = {}
    to_create = []
    counter = 0
    for sentence in data:
        counter += 1
        meta.update(sentence.metadata)
        new_obj = {}
        new_obj.update(meta)

        sentence_id = counter
        sentence_obj = {
            "urn": f"urn:cite2:scaife-viewer:syntaxTree.v1:syntaxTree-daphne-{exemplar}-{sentence_id}",
            "treebank_id": sentence_id,
            "words": [],
        }
        passage_refs = dict()
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
            misc = token.get("misc") or {}
            ref = misc.get("Ref")
            if ref:
                passage_refs[f"{version_urn}{ref}"] = None

        # TODO: can't do cite or refs just yet, which will be required
        # This is likely something we could do from that sent_id as another
        # kind of lookup
        references = sentence.metadata.get("references")
        if references:
            references = [references]
        elif passage_refs:
            references = [urn for urn in passage_refs]
        elif references is None:
            # TODO: read from the file
            references = [f"{versionish_urn}{counter}"]
        else:
            references = []
        sentence_obj.update(
            {
                "references": references,
                "citation": str(sentence_id),
            }
        )
        to_create.append(sentence_obj)
    output_path = get_output_path(input_path)

    json.dump(
        to_create,
        open(output_path, "w"),
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    main()
