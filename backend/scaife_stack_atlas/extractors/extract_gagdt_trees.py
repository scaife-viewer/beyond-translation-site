import json
from pathlib import Path

from lxml import etree


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


def extract_trees(input_path, version_urn):
    with input_path.open() as f:
        tree = etree.parse(f)
    to_create = []
    version_part = version_urn.rsplit(":", maxsplit=2)[1]
    exemplar = version_part.replace(".", "-")
    for sentence in tree.xpath("//sentence"):
        seen_urns = set()
        sentence_id = sentence.attrib["id"]
        # TODO: Determine what we want to do with these namespaces across all of these projects.
        sentence_obj = {
            "urn": f'urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-{exemplar}-{sentence.attrib["id"]}',
            "treebank_id": sentence_id,
            "words": [],
        }
        last_cite = None
        for word in sentence.xpath(".//word"):
            id_val = word.attrib["id"]
            try:
                id_val = int(id_val)
            except ValueError:
                id_val = int(id_val.split(".").pop())

            head_val = word.attrib["head"]
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
            cite = word.attrib.get("cite")
            if cite:
                ref = cite.rsplit(":", maxsplit=1)[1]
                word_obj["ref"] = ref
                seen_urns.add(f"{version_urn}{ref}")
                if last_cite is None:
                    last_cite = cite
                if cite != last_cite:
                    word_obj["break_before"] = True
                    last_cite = cite
            sentence_obj["words"].append(word_obj)

        sentence_obj["words"] = transform_headwords(sentence_obj["words"])

        sentence_obj["references"] = sorted(list(seen_urns))
        subdoc = sentence.attrib.get("subdoc")
        if subdoc:
            citation = f"{subdoc} ({sentence_id})"
        else:
            citation = f"({sentence_id})"
        sentence_obj["citation"] = citation
        to_create.append(sentence_obj)
    return to_create


def main():
    input_paths = Path("data/raw/gregorycrane-gAGDT").glob("*.xml")
    for input_path in input_paths:
        work_part = input_path.name.split(".perseus-grc1")[0]
        version_part = f"{work_part}.perseus-grc2"
        version_urn = f"urn:cts:greekLit:{version_part}:"

        trees = extract_trees(input_path, version_urn)
        output_name = f"gregorycrane_gagdt_syntax_trees_{version_part}.json"
        output_path = Path("data/annotations/syntax-trees", output_name)
        json.dump(
            trees, output_path.open("w"), ensure_ascii=False, indent=2,
        )


if __name__ == "__main__":
    main()
