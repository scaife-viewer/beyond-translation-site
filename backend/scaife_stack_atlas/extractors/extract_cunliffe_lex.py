import json
import re
from pathlib import Path

from anytree import Node
from anytree.exporter import DictExporter
from lxml import etree


DEBUG_OUTPUT = False

TREE_EXPORTER = DictExporter()

TEI_NS = {"TEI": "http://www.tei-c.org/ns/1.0"}
ID_ATTRIB = "{http://www.w3.org/XML/1998/namespace}id"
CITATION_TAG = "{http://www.tei-c.org/ns/1.0}cit"
ENTRY_URN_PREFIX = "urn:cite2:exploreHomer:entries.atlas_v1:1."
sense_idx = 0


def get_sense_depth(elem):
    """
    Derive depth of sense from its ancestors.
    """
    offset = 3
    return len(list(elem.iterancestors())) - offset


def as_text(element):
    return (
        etree.tostring(element, method="text", encoding="utf-8").decode("utf-8").strip()
    )


def get_ref_from_bibl(element):
    if element is None:
        return None
    n = element.attrib.get("n")
    if n:
        return n.split("Hom. ")[1]
    return element.text


EXTRACTOR_PATTERN = re.compile(r"(?P<version>\w{2}\.)\s(?P<ref>.*)")
VERSION_ALIAS_LOOKUP = {
    "Il.": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
    "Od.": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:",
}


def process_as_sense(elem):
    for selector in {
        "{http://www.tei-c.org/ns/1.0}bibl",
        "{http://www.tei-c.org/ns/1.0}quote",
    }:
        match = elem.find(selector)
        if match is not None:
            return True
    return False


def ref_to_urn(ref):
    if not ref:
        return
    match = EXTRACTOR_PATTERN.match(ref)
    if not match:
        return
    alias, ref = match.groups()
    return f"{VERSION_ALIAS_LOOKUP[alias]}{ref}"


def process_sense(sibling):
    # FIXME: Refactor this
    global sense_idx
    senses = []
    cases = {
        "{http://www.tei-c.org/ns/1.0}p": "text",
        "{http://www.tei-c.org/ns/1.0}div": "sense",
        "{http://www.tei-c.org/ns/1.0}pb": "skip",
    }

    sense_head = sibling.find("{http://www.tei-c.org/ns/1.0}head", namespaces=TEI_NS)
    if sense_head is None:
        label = ""
        parts = sibling.iterchildren()
    else:
        label = as_text(sense_head)
        parts = sense_head.itersiblings()

    depth = get_sense_depth(sibling)

    for gchild in parts:
        case = cases[gchild.tag]
        if case == "text":
            sense_def_parts = []
            citationish = []
            is_cf_bibl = False
            for ggchild in gchild.iterchildren():
                if ggchild.tag in [
                    "{http://www.tei-c.org/ns/1.0}term",
                    "{http://www.tei-c.org/ns/1.0}gloss",
                ]:
                    def_value = as_text(ggchild)
                    if def_value:
                        sense_def_parts.append(def_value)
                elif ggchild.tag == "{http://www.tei-c.org/ns/1.0}cit":
                    quote_parts = []
                    for quote in ggchild.findall("{http://www.tei-c.org/ns/1.0}quote"):
                        # alaoo-cunliffe-lex
                        quote_parts.append(as_text(quote))
                        next_sibling = quote.getnext()
                        if (
                            next_sibling is not None
                            and next_sibling.tag == "{http://www.tei-c.org/ns/1.0}note"
                        ):
                            quote_parts.append(
                                etree.tostring(
                                    next_sibling, method="text", encoding="utf-8",
                                ).decode("utf-8")
                            )

                    if quote_parts:
                        quote_text = " ".join(quote_parts)
                    else:
                        # TODO:
                        quote_text = None

                    citationish.append(
                        {
                            # ref could be using the text, but we prefer the actual entry, for now
                            "ref": get_ref_from_bibl(
                                ggchild.find("{http://www.tei-c.org/ns/1.0}bibl")
                            ),
                            "quote": quote_text,
                        }
                    )
                    # TODO:
                    cf_str = (
                        ggchild.tail.strip().replace(".", "").strip()
                        if ggchild.tail
                        else ""
                    )
                    if cf_str == "Cf":
                        # FIXME: How to capture Cf in the sense
                        is_cf_bibl = True
                elif ggchild.tag == "{http://www.tei-c.org/ns/1.0}bibl":
                    quote = None
                    if not is_cf_bibl:
                        if ggchild.getprevious() is None or ggchild.getprevious().tag in {
                            "{http://www.tei-c.org/ns/1.0}gloss",
                            "{http://www.tei-c.org/ns/1.0}cit",
                            # aganos-cunliffe-lex-2"
                            "{http://www.tei-c.org/ns/1.0}foreign",
                            # agapazo-cunliffe-lex-1,
                            "{http://www.tei-c.org/ns/1.0}ref",
                            "{http://www.tei-c.org/ns/1.0}term",
                        }:
                            is_cf_bibl = True
                        else:
                            # FIXME: we are setting `is_cf_bibl` regardless
                            is_cf_bibl = True
                    citationish.append(
                        {"ref": get_ref_from_bibl(ggchild), "quote": None}
                    )
                elif ggchild.tag in {
                    "{http://www.tei-c.org/ns/1.0}foreign",
                    "{http://www.tei-c.org/ns/1.0}hi",
                    "{http://www.tei-c.org/ns/1.0}ref",
                    # aggelie-cunliffe-lex
                    "{http://www.tei-c.org/ns/1.0}quote",
                }:
                    sense_def_parts.append(as_text(ggchild))
                elif ggchild.tag in {
                    "{http://www.tei-c.org/ns/1.0}pb",
                }:
                    continue
                else:
                    pass
                    # raise NotImplementedError
            if not sense_def_parts:
                sense_def_parts.append(as_text(gchild))
            elif gchild.text:
                sense_def_parts[0] = f"{gchild.text}{sense_def_parts[0]}"

            sense_idx += 1
            sense_urn = f"urn:cite2:exploreHomer:senses.atlas_v1:1.{sense_idx}"
            citation_urn_part = sense_urn.rsplit(":")[-1]
            base_urn = f"urn:cite2:scholarlyEditions:citations.v1:{citation_urn_part}"

            citations = []
            for pos, citation in enumerate(citationish):
                cite_idx = pos + 1
                citation["urn"] = ref_to_urn(citation["ref"])
                citations.append({"urn": f"{base_urn}_{cite_idx}", "data": citation})
            sense_definition = " ".join(sense_def_parts).strip()
            if citations:
                def_splitter = citations[0]["data"]["ref"] or ""
                if def_splitter:
                    sense_definition = sense_definition.split(def_splitter)[0].strip()

            if DEBUG_OUTPUT:
                print(str(depth), label, sense_definition)

            senses.append(
                dict(
                    label=label,
                    level=depth,
                    definition=sense_definition,
                    citations=citations,
                    urn=sense_urn,
                )
            )
            if label:
                label = ""
                depth += 1
        elif case == "sense":
            if label:
                # ensure we process an otherwise "empty" sense
                # e.g. tithemi-cunliffe-lex-1

                sense_idx += 1
                sense_urn = f"urn:cite2:exploreHomer:senses.atlas_v1:1.{sense_idx}"

                if DEBUG_OUTPUT:
                    print(str(depth), label, "")

                senses.append(
                    dict(
                        label=label,
                        level=depth,
                        definition="",
                        citations=[],
                        urn=sense_urn,
                    )
                )
                # set label to blank for next iteration
                label = ""

            senses.extend(process_sense(gchild))
        else:
            raise NotImplementedError
    return senses


def get_parent(root, node, data):
    if node is None:
        return root
    elif data["level"] == node.level:
        return node.parent
    elif data["level"] > node.level:
        return node
    elif data["level"] < node.level:
        for ancestor in node.iter_path_reverse():
            if ancestor.level == data["level"]:
                return ancestor.parent
        return root
    assert False


def postprocess_senses(senses):
    """
    Convert the "level" information from the senses into
    a nested structure
    """
    root = Node("", level=0)
    node = None
    for sense in senses:
        parent = get_parent(root, node, sense)
        node = Node(
            sense["label"],
            label=sense["label"],
            urn=sense["urn"],
            parent=parent,
            definition=sense["definition"],
            level=sense["level"],
            citations=sense["citations"],
        )

    for node in root.descendants:
        delattr(node, "level")
        delattr(node, "name")

    try:
        # get the root's children
        return TREE_EXPORTER.export(root)["children"]
    except KeyError:
        # TODO: Log an error
        return []


def extract_entry(textpart):
    # TODO: Review this with @jtauber; Logeion doesn't seem to have them
    if textpart.attrib.get("n") in ["prefsuff"]:
        return

    head_el = textpart.find("{http://www.tei-c.org/ns/1.0}head", namespaces=TEI_NS)
    try:
        assert len(head_el) is not None
    except AssertionError:
        import pdb

        pdb.set_trace()

    head_text = as_text(head_el)
    if DEBUG_OUTPUT:
        print(head_text)

    # NOTE: Strip dagger to prevent an issue with lemma lookup
    head_text = head_text.strip("†")

    # head_text = " ".join([i.strip() for i in head_el.itertext()]).strip()
    siblings = head_el.itersiblings()
    cases = {
        "{http://www.tei-c.org/ns/1.0}p": "text",
        "{http://www.tei-c.org/ns/1.0}div": "sense",
        "{http://www.tei-c.org/ns/1.0}pb": "skip",
    }
    entry_defparts = []
    senses = []
    for sibling in siblings:
        if sibling.tag not in cases:
            raise NotImplementedError
        case = cases[sibling.tag]
        if case == "skip":
            continue
        elif case == "text":
            entry_defparts.append(as_text(sibling))
            # TODO: Further processing of "psudo-senses"
            # that have cit or bibl tags
        elif case == "sense":
            senses.extend(process_sense(sibling))

    senses = postprocess_senses(senses)
    return dict(
        headword=head_text,
        data={
            # TODO: Formatting here?  Review with how LGO was processed
            "content": " ".join([f"<p>{e.strip()}</p>" for e in entry_defparts])
            # "content": " ".join(entry_defparts).strip()
        },
        # id?
        senses=senses,
    )


def main():
    path = Path("data/raw/cunliffe/cunliffe.lexentries.unicode.xml")
    with path.open() as f:
        tree = etree.parse(f)
    path = "{http://www.tei-c.org/ns/1.0}div[@n]"
    entries = []
    entry_pos = 0
    for textpart in tree.find("//{http://www.tei-c.org/ns/1.0}body").iterfind(
        path, namespaces=TEI_NS
    ):
        entry = extract_entry(textpart)
        if entry:
            entry_pos += 1
            entry["urn"] = f"{ENTRY_URN_PREFIX}{entry_pos}"
            entries.append(entry)
    data = {
        "label": "A Lexicon of the Homeric Dialect (Cunliffe, Vol. 1)",
        "urn": "urn:cite2:scaife-viewer:dictionaries.v1:cunliffe-lex",
        "kind": "Dictionary",
        "entries": entries,
    }
    output_path = Path("data/annotations/dictionaries/cunliffe-1-lex.json")
    with output_path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
