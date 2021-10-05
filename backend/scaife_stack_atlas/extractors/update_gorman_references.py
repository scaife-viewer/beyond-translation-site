import json
from pathlib import Path


def main():
    input_path = Path(
        "data/annotations/syntax-trees/gorman_syntax_trees_tlg0059.tlg002.perseus-grc1.json"
    )

    version = "urn:cts:greekLit:tlg0059.tlg002.perseus-grc1-vgorman1-trees:"

    sentences = json.load(input_path.open())
    for sentence in sentences:
        _ = sentence.pop("references")
        passage = f'{version}{sentence["treebank_id"]}'
        sentence["references"] = [passage]
    json.dump(sentences, input_path.open("w"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
