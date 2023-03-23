import json
import os
from pathlib import Path

import django

import requests
from lxml import etree


# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

from scaife_viewer.atlas.urn import URN  # noqa


SV_ATLAS_GQL_ENDPOINT = "https://scaife.perseus.org/atlas/graphql/"


class NoVersionFound(Exception):
    pass


def get_atlas_versions():
    gql_query = """
    {
    versions {
        edges {
        node {
            label
            urn
            lang
        }
        }
    }
    }
    """
    resp = requests.post(SV_ATLAS_GQL_ENDPOINT, data={"query": gql_query})
    if resp.ok:
        edges = resp.json()["data"]["versions"]["edges"]
        nodes = [e["node"] for e in edges]
        return nodes


def transform_headwords(words):
    inbounds = set(w["id"] for w in words)
    for word in words:
        if word["head_id"] not in inbounds:
            # NOTE: This is likely from a sentence id that has been split
            # into sub-sentences; if the `head_id` is not in the split sentence,
            # we interpret this as being the "new" oort
            word["original_head_id"] = word["head_id"]
            word["head_id"] = 0
    return words


def extract_language(root):
    treebank = root.xpath("//treebank")[0]
    return treebank.attrib["{http://www.w3.org/XML/1998/namespace}lang"]


def build_base_urn(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]
    collection = "glaux"
    return f"urn:cite2:beyond-translation:syntaxTree.atlas_v1:{collection}-{tgp}-{wp}"


def fetch_version(input_path, versions_lu):
    stem = input_path.stem
    tg, work = stem.split("-")
    work_part = f"tlg{tg}.tlg{work}"
    candidates = filter(lambda x: x["urn"].count(work_part), versions_lu)
    grc_candidate = next(iter(filter(lambda x: x["lang"] == "grc", candidates)), None)
    if not grc_candidate:
        raise NoVersionFound(input_path)
    return grc_candidate


def extract_trees(input_path, versions_lu):
    with input_path.open() as f:
        tree = etree.parse(f)

    lang = extract_language(tree)
    version = fetch_version(input_path, versions_lu)
    if not version:
        return None, None

    version_urn = URN(version["urn"])

    # NOTE: We may want to revisit how this is extracted between gAGDT
    # and Gorman trees
    # version = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"

    # TODO: Refactor these URNs using a collection
    base_urn = build_base_urn(version_urn)
    to_create = []
    for sentence in tree.xpath("//sentence"):
        seen_urns = set()
        sentence_id = sentence.attrib["id"]
        # TODO: Determine what we want to do with these namespaces across all of these projects.
        sentence_obj = {
            "urn": f'{base_urn}-{lang}-{sentence.attrib["id"]}',
            "treebank_id": sentence_id,
            "words": [],
        }
        # FIXME: This seems pretty specific to books / lines
        subdoc = sentence.get("subdoc", "")
        # 1.1-1.7
        passage_ref_root = subdoc.split("-")[0].split(".")[0]
        # 1
        if passage_ref_root:
            passage_ref_root = int(passage_ref_root)
        else:
            passage_ref_root = None
        # TODO: Other additional data in 'ref'; e.g. subdoc
        last_cite = None
        for word in sentence.xpath(".//word"):
            id_val = word.attrib["id"]
            try:
                id_val = int(id_val)
            except ValueError:
                id_val = int(id_val.split(".").pop())

            head_val = word.attrib["head"]
            if not head_val:
                head_val = 0
            try:
                head_val = int(head_val)
            except ValueError:
                head_val = int(head_val.split(".").pop())
            word_obj = {
                "id": id_val,
                "value": word.attrib["form"],
                "head_id": head_val,
                "relation": word.attrib["relation"],
                "lemma": word.attrib.get("lemma", ""),
                "tag": word.attrib.get("postag", ""),
            }
            cite = word.attrib.get("line")
            if cite:
                # ref = line.rsplit(":", maxsplit=1)[1]
                ref = f"{passage_ref_root}.{cite}"
                word_obj["ref"] = ref
                seen_urns.add(f"{version_urn}{ref}")
                if last_cite is None:
                    last_cite = cite
                if cite != last_cite:
                    word_obj["break_before"] = True
                    last_cite = cite
            sentence_obj["words"].append(word_obj)

        sentence_obj["words"] = transform_headwords(sentence_obj["words"])

        document_id = sentence.attrib.get("document_id")
        subdoc = sentence.attrib.get("subdoc")
        if document_id and subdoc:
            ref = subdoc
            seen_urns.add(f"{version_urn}{ref}")

        # TODO: We need to handle this better
        # assert sentence_obj["references"]
        # TODO: This might need to change
        sentence_obj["references"] = sorted(list(seen_urns))
        # TODO: ref data e.g. PER|0012-001|2274106
        if subdoc:
            citation = f"{subdoc} ({sentence_id})"
        else:
            print(sentence_id)
            citation = None
        sentence_obj["citation"] = citation
        to_create.append(sentence_obj)
    return version_urn, to_create


def process_directory(input_dir):
    output_dir = Path("data/annotations/syntax-trees")
    output_dir.mkdir(parents=True, exist_ok=True)
    idx = 1
    # TODO: Resolve problems or improve logging
    problems = []
    versions_lu = get_atlas_versions()
    try:
        paths = input_dir.glob("*.xml")
        paths = [Path('data/raw/glaux-trees/0012-001.xml')]
        for input_path in paths:
            try:
                version_urn, trees = extract_trees(input_path, versions_lu)
            except NoVersionFound:
                print(f"No version found: {input_path.stem}")
                version_urn = trees = None

            if not version_urn and not trees:
                print(f"Could not extract data from {input_path.name}")
                problems.append(input_path.name)
                continue
            prefix = "glaux_syntax_trees"
            tgp = version_urn.parsed["textgroup"]
            wp = version_urn.parsed["work"]
            vp = version_urn.parsed["version"]

            # TODO: Combine trees from the same version; we append idx for now.
            annotation_basename = f"{prefix}_{str(idx).zfill(3)}_{tgp}.{wp}.{vp}.json"
            output_path = Path(output_dir, annotation_basename)
            json.dump(
                trees, output_path.open("w"), ensure_ascii=False, indent=2,
            )
            idx += 1
    except Exception as excep:
        import ipdb

        ipdb.set_trace()
        raise excep
    print("\n".join(problems))


def main():
    input_dir = Path("data/raw/glaux-trees")
    process_directory(input_dir)


if __name__ == "__main__":
    main()
