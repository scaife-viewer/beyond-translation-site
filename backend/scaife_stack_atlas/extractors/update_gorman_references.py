import json
import os
from pathlib import Path

import django

# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

from scaife_viewer.atlas.urn import URN  # noqa


def get_paths():
    syntax_trees_dir = Path("data/annotations/syntax-trees")
    return syntax_trees_dir.glob("gorman_*")


def update_references(input_path):
    sentences = json.load(input_path.open())
    version_urn = None
    for sentence in sentences:
        if version_urn is None and sentence["references"]:
            # TODO: handle where version is not identified; perhaps add version
            # to annotation collection spec?
            version = URN(sentence["references"][0]).up_to(URN.VERSION)
            version_urn = URN(version)
            break

    version_part = str(version_urn)[:-1]
    exemplar_part = "vgorman1-trees"
    version = f"{version_part}-{exemplar_part}:"

    for sentence in sentences:
        references = sentence["references"]
        if references:
            passage = f'{version}{sentence["treebank_id"]}'
            sentence["references"] = [passage]
    json.dump(sentences, input_path.open("w"), indent=2, ensure_ascii=False)


def main():
    for path in get_paths():
        update_references(path)


if __name__ == "__main__":
    main()
