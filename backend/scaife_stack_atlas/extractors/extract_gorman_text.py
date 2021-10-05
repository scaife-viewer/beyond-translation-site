import json
from pathlib import Path


def extract_refs_and_lines(input_path):
    """
    Extract sentences as refs and lines
    """
    sentences = json.load(input_path.open())
    refs_and_lines = []
    for sentence in sentences:
        line = []
        for word in sentence["words"]:
            # TODO: Regex for punctuation
            if word["value"] in [",", ".", "·", ";"]:
                line[-1] += word["value"]
            elif word["value"] == "[0]":
                # NOTE: This won't work if we store trees as tokens
                continue
            else:
                line.append(word["value"])
        ref = f'{sentence["treebank_id"]}.'
        refs_and_lines.append((ref, " ".join(line)))
    return refs_and_lines


def write_text(output_path, refs_and_lines):
    """
    Write the text out to the ATLAS / text-server flat file format.
    """
    with output_path.open("w") as f:
        for row in refs_and_lines:
            print(" ".join(row), file=f)


def main():
    input_path = Path(
        "data/annotations/syntax-trees/gorman_syntax_trees_tlg0059.tlg002.perseus-grc1.json"
    )
    refs_and_lines = extract_refs_and_lines(input_path)
    output_path = Path(
        "data/library/tlg0059/tlg002/tlg0059.tlg002.perseus-grc1-vgorman1-trees.txt"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(output_path, refs_and_lines)


if __name__ == "__main__":
    main()
