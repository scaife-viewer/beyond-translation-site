import json
import os
from pathlib import Path

import django

from lxml import etree

# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

from scaife_viewer.atlas.urn import URN  # noqa


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


def extract_version(sentence):
    value = sentence.attrib["document_id"]
    if value.startswith("urn"):
        urn = value
    elif value.startswith("http://perseids.org/annotsrc/"):
        urn = value.split("http://perseids.org/annotsrc/")[1]
    else:
        print(value)
        return None
    return f"{urn}:"


def extract_language(root):
    treebank = root.xpath("//treebank")[0]
    return treebank.attrib["{http://www.w3.org/XML/1998/namespace}lang"]


def build_base_urn(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]
    return f"urn:cite2:beyond-translation:syntaxTree.atlas_v1:{tgp}-{wp}"


def extract_trees(input_path):
    with input_path.open() as f:
        tree = etree.parse(f)

    lang = extract_language(tree)
    version = extract_version(tree.xpath("//sentence")[0])
    if not version:
        return None, None

    version_urn = URN(version)

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
            sentence_obj["words"].append(word_obj)

        sentence_obj["words"] = transform_headwords(sentence_obj["words"])

        document_id = sentence.attrib.get("document_id")
        subdoc = sentence.attrib.get("subdoc")
        if document_id and subdoc:
            ref = subdoc
            seen_urns.add(f"{version_urn}{ref}")

        # TODO: We need to handle this better
        # assert sentence_obj["references"]
        sentence_obj["references"] = sorted(list(seen_urns))

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
    try:
        for input_path in input_dir.glob("*.xml"):
            version_urn, trees = extract_trees(input_path)
            if not version_urn and not trees:
                print(f"Could not extract data from {input_path.name}")
                problems.append(input_path.name)
                continue
            prefix = "gorman_syntax_trees"
            tgp = version_urn.parsed["textgroup"]
            wp = version_urn.parsed["work"]
            vp = version_urn.parsed["version"]

            # TODO: Combine trees from the same version; we append idx for now.
            annotation_basename = f"{prefix}_{idx}_{tgp}.{wp}.{vp}.json"
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
    input_dir = Path("data/raw/gorman-trees")
    process_directory(input_dir)


if __name__ == "__main__":
    main()
