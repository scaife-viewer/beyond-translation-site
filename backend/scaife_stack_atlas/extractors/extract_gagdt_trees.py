import json
from pathlib import Path

from lxml import etree


def transform_headwords(words):
    inbounds = set(w["id"] for w in words)
    for word in words:
        if word["head_id"] not in inbounds:
            # NOTE: This is likely from a sentence id that has been split
            # into sub-sentences; if the `head_id` is not in the split sentence,
            # we interpret this as being the "new" root
            word["original_head_id"] = word["head_id"]
            word["head_id"] = 0
    return words


def _mapped_role(value):
    # TODO: We're skipping these other roles for now
    return {
        # "supervisor": "Supervisor",
        "annotator of the text": "Annotator",
        # "release editor: post-annotation normalization and harmonization": "Release Editor",
        # "responsible for the annotation environment and cts:urn technology": "Annotation Environment",
    }.get(value, None)


def _sort_records(records):
    weight_lookup = {
        "Supervisor": 4,
        "Annotator": 1,
        "Release Editor": 2,
        "Annotation Environment": 3,
    }
    return sorted(records, key=lambda x: weight_lookup[x["role"]])


def extract_attribution_info(input_path):
    records = []
    with input_path.open() as f:
        tree = etree.parse(f)

    for statement in tree.xpath("//respStmt"):
        record = dict()

        resp = statement.find("resp")
        if resp is not None:
            record["role"] = resp.text
        else:
            record["role"] = statement.find("persName").find("resp").text

        record["role"] = _mapped_role(record["role"])
        if not record["role"]:
            continue

        pers = statement.find("persName")

        name = pers.find("name")
        if name is not None:
            record["person"] = dict(name=name.text)
            record["_short_name"] = pers.find("short").text
        else:
            record["person"] = dict(name=pers.text)

        address = pers.find("address")
        if address is not None:
            record["organization"] = dict(name=address.text)
            name
        else:
            value = statement.find("address")
            record["organization"] = dict(name=value.text)

        record["data"] = {"references": []}

        records.append(record)

    return _sort_records(records)


def get_records_lookup(records):
    records_lookup = {}
    for record in records:
        key = record.pop("_short_name")
        records_lookup[key] = record
    return records_lookup


def update_attributions(sentence, records_lookup, urn):
    short_names = [elem.text for elem in sentence.xpath(".//primary | .//secondary")]
    for short_name in short_names:
        try:
            annotator = records_lookup[short_name]
        except KeyError as excep:
            if short_name == "millermo2":
                annotator = records_lookup["millermo"]
            elif short_name in ["david.bamman", "gleason"]:
                continue
            else:
                raise excep
        annotator["data"]["references"].append(urn)


def extract_trees(input_path, version_urn, records_lookup):
    with input_path.open() as f:
        tree = etree.parse(f)
    to_create = []
    version_part = version_urn.rsplit(":", maxsplit=2)[1]
    print(f"Extracting from {version_part}")
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

        update_attributions(sentence, records_lookup, sentence_obj["urn"])

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
                try:
                    head_val = int(head_val.split(".").pop())
                except ValueError:
                    head_val = None

            if head_val is None:
                print(
                    f'No @head found [form={word.attrib["form"]} sentence_id={sentence_id}]'
                )
                continue

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

        records = extract_attribution_info(input_path)
        records_lookup = get_records_lookup(records)

        trees = extract_trees(input_path, version_urn, records_lookup)

        # Write out trees
        output_name = f"gregorycrane_gagdt_syntax_trees_{version_part}.json"
        output_path = Path("data/annotations/syntax-trees", output_name)
        json.dump(
            trees,
            output_path.open("w"),
            ensure_ascii=False,
            indent=2,
        )

        # Write out attributions
        output_name = (
            f"attributions_gregorycrane_gagdt_syntax_trees_{version_part}.json"
        )
        output_path = Path("data/annotations/attributions", output_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(
            list(records_lookup.values()),
            output_path.open("w"),
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    main()
