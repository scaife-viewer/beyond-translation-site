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


def extract_trees(input_path):
    exemplar = "grc"
    with input_path.open() as f:
        tree = etree.parse(f)
    version = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
    to_create = []
    for sentence in tree.xpath("//sentence"):
        seen_urns = set()
        sentence_id = sentence.attrib["id"]
        # TODO: Determine what we want to do with these namespaces across all of these projects.
        sentence_obj = {
            "urn": f'urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-{exemplar}-{sentence.attrib["id"]}',
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
                seen_urns.add(f"{version}{ref}")
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
    input_path = Path("data/raw/gregorycrane-gAGDT/tlg0012.tlg001.perseus-grc1.tb.xml")
    trees = extract_trees(input_path)
    output_path = Path(
        "data/annotations/syntax-trees/gregorycrane_gagdt_syntax_trees_tlg0012.tlg001.perseus-grc2.json"
    )
    json.dump(
        trees, output_path.open("w"), ensure_ascii=False, indent=2,
    )


if __name__ == "__main__":
    main()
