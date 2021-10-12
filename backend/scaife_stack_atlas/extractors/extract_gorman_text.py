import os
import json
import time
from pathlib import Path

import requests
import django

# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

from scaife_viewer.atlas.urn import URN  # noqa

SV_ATLAS_GQL_ENDPOINT = "https://scaife.perseus.org/atlas/graphql/"
SV_ATLAS_THROTTLE_DURATION = 0.1

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
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        tg_urn = version_urn.up_to(URN.TEXTGROUP)
        gql_query = """{
            textGroups(urn: "%s") {
                edges {
                node {
                    label
                }
                }
            }
        }""" % (tg_urn)
        resp = requests.post(SV_ATLAS_GQL_ENDPOINT, data={
            "query": gql_query
        })
        if resp.ok:
            edges = resp.json()["data"]["textGroups"]["edges"]

            try:
                node = edges[0]["node"]
                label = node["label"]
            except:
                msg = f"No textgroup found: {tg_urn}"
                print(msg)
                label = version_urn.parsed["textgroup"]

            data = {
                "urn": tg_urn,
                "node_kind": "textgroup",
                "name": [{"lang": "eng", "value": label,}],
            }
            with metadata_path.open("w") as f:
                json.dump(data, f, indent=2)
            time.sleep(SV_ATLAS_THROTTLE_DURATION)


def ensure_work_metadata(version_urn, w_path):
    metadata_path = Path(w_path, "metadata.json")
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        work_urn = version_urn.up_to(URN.WORK)
        gql_query = """{
            tree(urn: "%s") {
                tree
            }
        }""" % (work_urn)
        resp = requests.post(SV_ATLAS_GQL_ENDPOINT, data={
            "query": gql_query
        })
        if resp.ok:
            try:
                tree = resp.json()["data"]["tree"]["tree"]
                work_metadata = tree[0]["data"]["metadata"]
                version_metadata = tree[0]["children"][0]["data"]["metadata"]
            except:
                msg = f"No work found: {work_urn}"
                print(msg)
                work_metadata = {"label": version_urn.parsed["work"], "lang": "grc"}
                version_metadata = {"label": version_urn.parsed["version"]}

            data = {
                "urn": version_urn.up_to(URN.WORK),
                "group_urn": version_urn.up_to(URN.TEXTGROUP),
                "node_kind": "work",
                "lang": work_metadata["lang"],
                "title": [{"lang": "eng", "value": work_metadata["label"]}],
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
                                "value": f'{version_metadata["label"]} (sentences)',
                            }
                        ],
                        "description": [
                            {"lang": "eng", "value": "Extracted from vgorman1 trees",}
                        ],
                    }
                ],
            }
            with metadata_path.open("w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            time.sleep(SV_ATLAS_THROTTLE_DURATION)


def stub_metadata(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]

    tg_path = Path(f"data/library/{tgp}")
    ensure_tg_metadata(version_urn, tg_path)

    w_path = Path(tg_path, wp)
    version_part = str(version_urn)[:-1]
    exemplar_part = "vgorman1-trees"

    if not version_part.endswith(exemplar_part):
        versionish_urn = URN(f"{version_part}-{exemplar_part}:")
    else:
        versionish_urn = version_urn

    ensure_work_metadata(versionish_urn, w_path)


def get_output_path(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]
    vp = version_urn.parsed["version"]
    workpart_path = Path(f"data/library/{tgp}/{wp}")

    exemplar_part = "vgorman1-trees"
    if not vp.endswith(exemplar_part):
        version_part = f"{vp}-{exemplar_part}"
    else:
        version_part = vp

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
