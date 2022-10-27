import json
import os
from collections import defaultdict
from pathlib import Path

import django


# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

from scaife_viewer.atlas.urn import URN  # noqa


EXEMPLAR_PART = "glaux-grc"
COLLETION_NAME = "glaux"


def get_paths():
    syntax_trees_dir = Path("data/annotations/syntax-trees")
    return sorted(syntax_trees_dir.glob(f"{COLLETION_NAME}_*"))


def update_references(workpart_counter, input_path):
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
    if not version_part.endswith(EXEMPLAR_PART):
        version = URN(f"{version_part}-{EXEMPLAR_PART}:")
    else:
        version = version_urn

    work_urn = str(version_urn.up_to(URN.WORK))
    counter = workpart_counter[work_urn]
    for sentence in sentences:
        passage = f"{version}{counter + 1}"
        sentence["references"] = [passage]
        counter += 1
    workpart_counter[work_urn] = counter
    json.dump(sentences, input_path.open("w"), indent=2, ensure_ascii=False)


def main():
    workpart_counter = defaultdict(int)
    for path in get_paths():
        update_references(workpart_counter, path)


if __name__ == "__main__":
    main()
