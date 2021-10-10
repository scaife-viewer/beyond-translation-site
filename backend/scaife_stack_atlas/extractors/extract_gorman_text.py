import os
import json
from pathlib import Path

import django

# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

from scaife_viewer.atlas.urn import URN  # noqa


def extract_version_refs_and_lines(input_path):
    """
    Extract sentences as refs and lines
    """
    sentences = json.load(input_path.open())
    refs_and_lines = []
    version_urn = None
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

        if version_urn is None and sentence["references"]:
            # TODO: handle where version is not identified; perhaps add version
            # to annotation collection spec?
            version = URN(sentence["references"][0]).up_to(URN.VERSION)
            version_urn = URN(version)

    return version_urn, refs_and_lines


def write_text(output_path, refs_and_lines):
    """
    Write the text out to the ATLAS / text-server flat file format.
    """
    with output_path.open("w") as f:
        for row in refs_and_lines:
            print(" ".join(row), file=f)


def get_paths():
    syntax_trees_dir = Path("data/annotations/syntax-trees")
    return syntax_trees_dir.glob("gorman_*")


def extract_text(input_path):
    version_urn, refs_and_lines = extract_version_refs_and_lines(input_path)
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]
    vp = version_urn.parsed["version"]
    output_path = Path(f"data/library/{tgp}/{wp}/{tgp}.{wp}.{vp}-vgorman1-trees.txt")
    # TODO: Handle where output path already exists; likely we need to
    # combine texts when we're doing the extraction
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(output_path, refs_and_lines)
    # TODO: Write out metadata too


def main():
    paths = get_paths()
    for path in paths:
        extract_text(path)


if __name__ == "__main__":
    main()
