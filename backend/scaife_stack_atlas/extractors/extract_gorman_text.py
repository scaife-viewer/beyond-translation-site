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


def ensure_tg_metadata(version_urn, tg_path):
    metadata_path = Path(tg_path, "metadata.json")
    if not metadata_path.exists():
        data = {
            "urn": version_urn.up_to(URN.TEXTGROUP),
            "node_kind": "textgroup",
            "name": [{"lang": "eng", "value": version_urn.parsed["textgroup"],}],
        }
        with metadata_path.open("w") as f:
            json.dump(data, f, indent=2)


def ensure_work_metadata(version_urn, w_path):
    metadata_path = Path(w_path, "metadata.json")
    if not metadata_path.exists():
        data = {
            "urn": version_urn.up_to(URN.WORK),
            "group_urn": version_urn.up_to(URN.TEXTGROUP),
            "node_kind": "work",
            "lang": "grc",  # TODO: Extract this?
            "title": [{"lang": "eng", "value": version_urn.parsed["work"]}],
            "versions": [
                {
                    "urn": str(version_urn),
                    "node_kind": "version",
                    "version_kind": "edition",
                    "lang": "grc",  # TODO: Extract this?
                    "first_passage_urn": f"{version_urn}1",
                    "citation_scheme": ["sentence"],
                    "label": [
                        {
                            "lang": "eng",
                            "value": f'{version_urn.parsed["version"]} (sentences)',
                        }
                    ],
                    "description": [
                        {"lang": "eng", "value": "Extracted from vgorman1 trees",}
                    ],
                }
            ],
        }
        with metadata_path.open("w") as f:
            json.dump(data, f, indent=2)


def stub_metadata(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]

    tg_path = Path(f"data/library/{tgp}")
    ensure_tg_metadata(version_urn, tg_path)

    w_path = Path(tg_path, wp)
    version_part = str(version_urn)[:-1]
    exemplar_part = "vgorman1-trees"
    versionish_urn = URN(f"{version_part}-{exemplar_part}:")
    ensure_work_metadata(versionish_urn, w_path)


def get_output_path(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]
    vp = version_urn.parsed["version"]
    workpart_path = Path(f"data/library/{tgp}/{wp}")
    version_part = f"{vp}-vgorman1-trees"
    return Path(workpart_path, f"{tgp}.{wp}.{version_part}.txt")


def extract_text(input_path):
    version_urn, refs_and_lines = extract_version_refs_and_lines(input_path)
    output_path = get_output_path(version_urn)

    # TODO: Replace with actual metadata
    stub_metadata(version_urn)

    # TODO: Handle where output path already exists; likely we need to
    # combine texts when we're doing the extraction
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(output_path, refs_and_lines)


def main():
    paths = get_paths()
    for path in paths:
        extract_text(path)


if __name__ == "__main__":
    main()
