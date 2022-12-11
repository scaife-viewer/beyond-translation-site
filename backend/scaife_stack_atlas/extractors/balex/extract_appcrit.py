import json
import re
from collections import defaultdict
from pathlib import Path

from lxml import etree


ns = {"TEI": "http://www.tei-c.org/ns/1.0"}


# TODO: Add this to scaife-viewer-atlas library
# h/t https://stackoverflow.com/questions/7100242/python-numpy-first-occurrence-of-subarray
def find_rk(seq, subseq):
    n = len(seq)
    m = len(subseq)
    if seq[:m] == subseq:
        yield 0
    hash_subseq = sum(hash(x) for x in subseq)  # compute hash
    curr_hash = sum(hash(x) for x in seq[:m])  # compute hash
    for i in range(1, n - m + 1):
        curr_hash += hash(seq[i + m - 1]) - hash(seq[i - 1])  # update hash
        if hash_subseq == curr_hash and seq[i : i + m] == subseq:
            yield i


def extract_readings(parsed):
    # FIXME: Refactor with extract_text
    version_urn = "urn:cts:latinLit:phi0428.phi001.dll-ed-lat1:"
    edition = parsed.find("//TEI:div[@type='edition']", namespaces=ns)
    chapters = edition.findall("TEI:p", namespaces=ns)
    parts = defaultdict(list)
    readings = []
    for chapter in chapters:
        chapter_ref = chapter.attrib["n"]
        # TODO: Handle chapter.seg refs
        ref = f"{chapter_ref}"
        parts[chapter_ref] = []
        segments = chapter.findall("TEI:seg", namespaces=ns)
        for segment in segments:
            text_content = []
            segment_ref = segment.attrib["n"]
            segment_text = segment.text
            if segment_text is not None:
                text_content.append(segment_text)
            for app in segment.findall("TEI:app", namespaces=ns):
                for lem in app.findall("TEI:lem", namespaces=ns):
                    lem_text = re.sub(r"\s+", " ", lem.xpath("string()").strip())
                    text_content.append(lem_text)
                    try:
                        lem_tokens = lem_text.split()
                    except Exception as e:
                        import ipdb

                        ipdb.set_trace()
                        raise e

                    # TODO: Refactor using subrefs

                    prior = parts.get(chapter_ref, [])
                    parts_ws = []
                    for p in prior:
                        parts_ws.extend(p[1].split())
                    try:
                        parts_ws.extend("".join(text_content).split())
                    except Exception as e:
                        import ipdb

                        ipdb.set_trace()
                        raise e

                    witnesses = lem.attrib.get("wit", "").split()
                    witnesses = lem.attrib.get("wit", "").split()
                    witnesses.extend(lem.attrib.get("source", "").split())

                    # TODO: Re-use for CITE URNs?
                    # TODO: Tighten this selector up
                    try:
                        lem_id = lem.attrib["{http://www.w3.org/XML/1998/namespace}id"]
                    except Exception:
                        lem_id = None

                    # NOTE: These were the instances where we couldn't compute
                    # token offsets; even if we move to CTS subreferences, we
                    # would still hit this problem
                    corrected_tokens = {
                        ("multaque",): ["temerarii—multaque"],
                        ("castra",): ["remotis—castra"],
                        ("quod", "uel"): ["accessiones—quod", "uel"],
                        ("nihilo",): ["tempestate—nihilo"],
                    }
                    correct_tokens = corrected_tokens.get(tuple(lem_tokens), lem_tokens)
                    try:
                        start_pos = next(find_rk(parts_ws, correct_tokens))
                        end_pos = start_pos + len(correct_tokens)
                    except Exception:
                        print(tuple(lem_tokens))
                        print(parts_ws)
                        # Found 4 problems, due to dashes; how could we solve this programatically?

                        import ipdb

                        ipdb.set_trace()
                        continue

                    token_range = range(start_pos, end_pos)
                    ve_refs = []
                    for idx in token_range:
                        ve_refs.append(f"{ref}.t{idx + 1}")
                    try:
                        assert len(ve_refs) == len(lem_tokens)
                    except Exception:
                        import ipdb

                        ipdb.set_trace()
                    readings.append(
                        dict(
                            witnesses=witnesses,
                            references=[f"{version_urn}{ref}"],
                            commentary=f"<span>{lem_text}</span>",
                            # FIXME: Construct fragment_verbose
                            fragment=lem_text,
                            # FIXME: sort key should just be an idx
                            # FIXME: URNs
                            ve_refs=ve_refs,
                        )
                    )

                    for rdg in app.findall("TEI:rdg", namespaces=ns):
                        # TODO: Re-use for CITE URNs
                        try:
                            rdg_id = rdg.attrib[
                                "{http://www.w3.org/XML/1998/namespace}id"
                            ]
                        except Exception:
                            rdg_id = None
                        # rdg_value = rdg.text or "".join(lem_text) or text
                        rdg_value = rdg.text
                        if rdg_value is None:
                            # rdg-13.5-cursu-litore
                            rdg_value = "".join(rdg.itertext())
                        noteish = rdg.getnext()
                        try:
                            if noteish is not None and noteish.tag.endswith("note"):
                                rdg_value = f"{rdg_value} {noteish.text}"
                        except Exception:
                            # 'rdg-19.6-lacuna-start
                            pass
                        if rdg_value is not None:
                            rdg_value = re.sub(r"\s+", " ", rdg_value.strip())
                        else:
                            import ipdb

                            ipdb.set_trace()

                        witnesses = rdg.attrib.get("wit", "").split()
                        witnesses.extend(rdg.attrib.get("source", "").split())
                        witnesses = [w.strip(",") for w in witnesses]
                        readings.append(
                            dict(
                                witnesses=witnesses,
                                references=[f"{version_urn}{ref}"],
                                commentary=f"<span>{rdg_value}</span>",
                                # FIXME: fragment_verbose
                                fragment=lem_text,
                                # FIXME: sort key should just be an idx
                                # FIXME: URNs
                                ve_refs=ve_refs,
                            )
                        )
                tail = app.tail
                if tail:
                    text_content.append(tail)
            text_content.append(" ")
            text_content = [s for s in text_content if s]
            text_content = "".join(
                [re.sub(r"\s+", " ", s) for s in text_content if re.sub(r"\s+", " ", s)]
            ).strip()
            parts[chapter_ref].append((segment_ref, text_content))
    return parts, readings


def extract_witnesses(parsed):
    # TODO: We are resolving witness, bibl and person;
    # we might want to classify those differently in the UX.
    lookup = {}
    for witness in parsed.xpath("//TEI:witness", namespaces=ns):
        key = witness.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        # FIXME: Improve formatting, e.g.
        # label = "".join(witness.xpath("descendant-or-self::text()")).strip()
        label = "".join(witness.xpath("text()")).strip()
        if not label:
            # TODO: We may want further special-casing to render the text version
            label = "".join(witness.xpath("descendant-or-self::text()")).strip()
        label = re.sub(r"\s+", " ", label)
        label = label.strip(" URL:").strip()
        lookup[key] = label
        # FIXME: Handling nesting of children like Uac or Uc, Head, etc

    for witness in parsed.xpath("//TEI:listBibl/TEI:bibl", namespaces=ns):
        key = witness.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        # FIXME: Additional formatting, as above
        label = "".join(witness.xpath("descendant-or-self::text()")).strip()
        label = re.sub(r"\s+", " ", label)
        label = label.strip(" URL:").strip()
        label = label.strip(key).strip()
        lookup[key] = label

    for witness in parsed.xpath("//TEI:listPerson/TEI:person", namespaces=ns):
        key = witness.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        # FIXME: Additional formatting, as above
        label = "".join(witness.xpath("descendant-or-self::text()")).strip()
        label = re.sub(r"\s+", " ", label)
        label = label.strip(" URL:").strip()
        label = label.strip(key).strip()
        lookup[key] = label

    return lookup


def process_readings(witness_lookup, readings):
    for idx, reading in enumerate(readings):
        reading["idx"] = str(idx)
        reading["urn"] = f"urn:cite2:scaife-viewer:commentary.v1:commentary{idx + 1}"
        witness_values = reading.pop("witnesses")
        witnesses = []
        for value in witness_values:
            key = value.strip("#")
            try:
                witnesses.append(dict(value=key, label=witness_lookup[key]))
            except KeyError:
                print(f"Witness key not found: {key}")
        reading["witnesses"] = witnesses
    return readings


def main():
    path = Path("data/raw/balex/ldlt-balex.xml")
    parsed = etree.parse(path.open("rb"))

    witness_lookup = extract_witnesses(parsed)
    _, readings = extract_readings(parsed)
    readings = process_readings(witness_lookup, readings)
    with Path(
        "data/annotations/text-annotations/text_annotations_phi0428.phi001.dll-lat1.json"
    ).open("w") as f:
        json.dump(readings, f, indent=2, ensure_ascii=False)


main()
