import json
import os
import time
from collections import defaultdict
from pathlib import Path

import django

import requests

from scaife_viewer.atlas.urn import URN  # noqa


# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()


SV_ATLAS_GQL_ENDPOINT = "https://scaife.perseus.org/atlas/graphql/"
SV_ATLAS_THROTTLE_DURATION = 0.1
EXEMPLAR_PART = "glaux-grc"
COLLETION_NAME = "glaux"


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
    return sorted(syntax_trees_dir.glob(f"{COLLETION_NAME}_*"))


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
        }""" % (
            tg_urn
        )
        resp = requests.post(SV_ATLAS_GQL_ENDPOINT, data={"query": gql_query})
        if resp.ok:
            edges = resp.json()["data"]["textGroups"]["edges"]

            try:
                node = edges[0]["node"]
                label = node["label"]
            except Exception:
                msg = f"No textgroup found: {tg_urn}"
                print(msg)
                label = version_urn.parsed["textgroup"]

            data = {
                "urn": tg_urn,
                "node_kind": "textgroup",
                "name": [{"lang": "eng", "value": label}],
            }
            with metadata_path.open("w") as f:
                json.dump(data, f, indent=2)
            time.sleep(SV_ATLAS_THROTTLE_DURATION)
    else:
        assert False


def ensure_work_metadata(version_urn, w_path):
    metadata_path = Path(w_path, "metadata.json")
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        work_urn = version_urn.up_to(URN.WORK)
        gql_query = """{
            tree(urn: "%s") {
                tree
            }
        }""" % (
            work_urn
        )
        resp = requests.post(SV_ATLAS_GQL_ENDPOINT, data={"query": gql_query})
        if resp.ok:
            try:
                tree = resp.json()["data"]["tree"]["tree"]
                work_metadata = tree[0]["data"]["metadata"]
                version_metadata = tree[0]["children"][0]["data"]["metadata"]
            except Exception:
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
                            {
                                "lang": "eng",
                                "value": "Extracted from {COLLECTION_NAME} trees",
                            }
                        ],
                    }
                ],
            }
            with metadata_path.open("w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            time.sleep(SV_ATLAS_THROTTLE_DURATION)
    else:
        assert False


def stub_metadata(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]

    tg_path = Path(f"data/library/{tgp}")
    ensure_tg_metadata(version_urn, tg_path)

    w_path = Path(tg_path, wp)
    version_part = str(version_urn)[:-1]
    exemplar_part = EXEMPLAR_PART

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

    exemplar_part = EXEMPLAR_PART
    if not vp.endswith(exemplar_part):
        version_part = f"{vp}-{exemplar_part}"
    else:
        version_part = vp

    return Path(workpart_path, f"{tgp}.{wp}.{version_part}.txt")


def build_refs_and_lines_lookup(paths):
    version_lookup = defaultdict(list)
    for path in paths:
        version_urn, refs_and_lines = extract_version_refs_and_lines(path)
        version_lookup[str(version_urn)].extend(refs_and_lines)
    return version_lookup


def rename_refs(version_lookup):
    for version_urn in version_lookup:
        refs_and_lines = version_lookup[version_urn]

        try:
            assert len(refs_and_lines) == len(
                set([ref for ref, line in refs_and_lines])
            )
        except AssertionError:
            old_refs_and_lines = refs_and_lines[::]
            refs_and_lines = []
            for pos, (ref, line) in enumerate(old_refs_and_lines):
                refs_and_lines.append((f"{pos + 1}.", line))
            try:
                assert len(refs_and_lines) == len(
                    set([ref for ref, line in refs_and_lines])
                )
            except AssertionError:
                import ipdb

                ipdb.set_trace()
                raise AssertionError

        version_lookup[version_urn] = refs_and_lines


def process_version(version, refs_and_lines):
    version_urn = URN(version)
    stub_metadata(version_urn)
    output_path = get_output_path(version_urn)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(output_path, refs_and_lines)


def main():
    paths = get_paths()
    version_lookup = build_refs_and_lines_lookup(paths)
    rename_refs(version_lookup)

    for version_urn, refs_and_lines in version_lookup.items():
        process_version(version_urn, refs_and_lines)


if __name__ == "__main__":
    main()
