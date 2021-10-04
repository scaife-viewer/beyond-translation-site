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
    # NOTE: We may want to revisit how this is extracted between gAGDT
    # and Gorman trees
    # version = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"

    # TODO: Refactor these URNs using a collection
    base_urn = "urn:cite2:beyond-translation:syntaxTree.atlasv1:tlg0059-tlg002"
    to_create = []
    for sentence in tree.xpath("//sentence"):
        seen_urns = set()
        sentence_id = sentence.attrib["id"]
        # TODO: Determine what we want to do with these namespaces across all of these projects.
        sentence_obj = {
            "urn": f'{base_urn}-{exemplar}-{sentence.attrib["id"]}',
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
            sentence_obj["words"].append(word_obj)

        sentence_obj["words"] = transform_headwords(sentence_obj["words"])

        document_id = sentence.attrib.get("document_id")
        subdoc = sentence.attrib.get("subdoc")
        if document_id and subdoc:
            _, version_part = document_id.split("http://perseids.org/annotsrc/")
            version = f"{version_part}:"
            ref = subdoc
            seen_urns.add(f"{version}{ref}")
        sentence_obj["references"] = sorted(list(seen_urns))

        if subdoc:
            citation = f"{subdoc} ({sentence_id})"
        else:
            print(sentence_id)
            citation = None
        sentence_obj["citation"] = citation
        to_create.append(sentence_obj)
    return to_create


def main():
    input_path = Path("data/raw/gorman-trees/plato apology.xml")
    trees = extract_trees(input_path)
    output_path = Path(
        "data/annotations/syntax-trees/gorman_syntax_trees_tlg0059.tlg002.perseus-grc1.json"
    )
    json.dump(
        trees, output_path.open("w"), ensure_ascii=False, indent=2,
    )


if __name__ == "__main__":
    main()
