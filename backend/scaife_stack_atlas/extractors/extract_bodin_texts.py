import json
import uuid
from pathlib import Path

from lxml import etree


DATA_DIR = Path("data")


def extract_from_text(path):
    parsed = etree.fromstring(path.read_bytes())
    sentences = []
    s_id_to_idx = {}
    idx_to_s_id = {}
    coarse_s_id_to_idx = {}
    idx = 0
    for sentence in parsed.iter("s"):
        # NOTE: We create our own referencing scheme (for simplicity)
        pos = idx + 1
        sentences.append(f"{pos}. {sentence.text}")
        # NOTE: Map the `id` attrib to our idx value
        s_id = sentence.attrib["id"]
        s_id_to_idx[s_id] = idx
        idx_to_s_id[idx] = s_id
        coarse_s_id = s_id.split(".")[0]
        coarse_s_id_to_idx.setdefault(coarse_s_id, []).append(idx)
        idx += 1
    return dict(
        sentences=sentences,
        s_id_to_idx=s_id_to_idx,
        idx_to_s_id=idx_to_s_id,
        coarse_s_id_to_idx=coarse_s_id_to_idx,
    )


def extract_alignment_records(t1_data, t2_data):
    alignments = {}
    for pos, t1_sentence in enumerate(t1_data["sentences"]):
        _, text = t1_sentence.split(" ", maxsplit=1)

        t1_idx = pos
        # figure out what the original s_id value was
        s_id = t1_data["idx_to_s_id"][t1_idx]
        coarse_s_id = s_id.split(".")[0]
        if coarse_s_id not in t2_data["coarse_s_id_to_idx"]:
            print(f'Data error; cannot find [id="{s_id}"] in the other document')
            continue

        t2_idxes = t2_data["coarse_s_id_to_idx"][coarse_s_id]
        t2_key = tuple(t2_idxes)
        alignments.setdefault(t2_key, []).append(t1_idx)

    flattened_alignments = []
    for lhs, rhs in alignments.items():
        flattened_alignments.append((list(lhs), rhs))
    reversed_alignments = []
    for (lhs, rhs) in flattened_alignments:
        reversed_alignments.append((rhs, lhs))
    return reversed_alignments


def generate_alignment_urn(slug):
    # TODO: Ensure unique URNs within scaife-viewer namespace
    minted_suffix = uuid.uuid4().hex
    return f"urn:cite2:scaife-viewer:alignment.v1:{slug}-{minted_suffix}"


def convert_to_tokens(version_urn, data, idxes):
    converted = []
    for idx in idxes:
        ref, text = data["sentences"][idx].split(". ", maxsplit=1)
        # 1
        # TODO: Ensure our tokenizer is working the same way
        tokens = text.split()
        for tidx, token in enumerate(tokens):
            pos = tidx + 1
            ve_ref = f"{ref}.t{pos}"
            converted.append(
                # FIXME: move to data
                f"{version_urn}{ve_ref}"
            )
    return converted


def convert_records_to_cts_refs(t1_data, t2_data, records):
    converted_records = []
    for (lhs, rhs) in records:
        converted_lhs = convert_to_tokens(
            "urn:cts:pdlpsci:bodin.livrep.ta-eng1:", t1_data, lhs
        )
        converted_rhs = convert_to_tokens(
            "urn:cts:pdlpsci:bodin.livrep.ta-fre1:", t2_data, rhs
        )
        converted_records.append((converted_lhs, converted_rhs))
    return converted_records


def write_alignment_annotation(label, alignment_urn, versions, alignment_records):
    shared_urn_part = alignment_urn.rsplit(":", maxsplit=1)[1]
    # FIXME: versions appending a ":"
    data = dict(
        urn=alignment_urn,
        label=label,
        format="atlas-standoff-annotation",
        # versions=[f"{urn}:" for urn in versions.keys()],
        versions=[f"{urn}" for urn in versions],
        records=[],
    )
    idx = 0
    for record in alignment_records:
        record_urn = (
            f"urn:cite2:scaife-viewer:alignment-record.v1:{shared_urn_part}_{idx}"
        )
        data["records"].append(
            dict(
                urn=record_urn,
                relations=record,
            )
        )
        idx += 1
    alignment_fname = f'{alignment_urn.rsplit(":", maxsplit=1)[1]}.json'
    path = Path(
        DATA_DIR,
        "annotations/text-alignments",
        alignment_fname,
    )
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_sentences(version_urn, lines):
    # TODO: Compare to Hafez
    part = version_urn.rsplit(":", maxsplit=2)[1]
    path = Path(
        DATA_DIR,
        "library/bodin/livrep",
        f"{part}.txt",
    )
    path.write_text("\n".join(lines))


def main():
    ENGLISH = Path(DATA_DIR, "raw/bodin-perl-nadel/english-to-french.xml")
    eng_data = extract_from_text(ENGLISH)

    FRENCH = Path(DATA_DIR, "raw/bodin-perl-nadel/french-to-english.xml")
    fra_data = extract_from_text(FRENCH)

    records = extract_alignment_records(eng_data, fra_data)
    # NOTE: We insert a record to pick up two lines that were not mapped
    records.insert(1, ([1, 2], []))
    cts_ref_records = convert_records_to_cts_refs(eng_data, fra_data, records)
    # alignment_urn = generate_alignment_urn("livrep-english-french-sentence-alignment")
    alignment_urn = "urn:cite2:scaife-viewer:alignment.v1:livrep-english-french-sentence-alignment-6d26700b93a44d1b929b6d959295c25d"
    versions = [
        "urn:cts:pdlpsci:bodin.livrep.ta-eng1:",
        "urn:cts:pdlpsci:bodin.livrep.ta-fre1:",
    ]
    write_alignment_annotation(
        "Livrep English / French Sentence Alignment",
        alignment_urn,
        versions,
        cts_ref_records,
    )

    write_sentences(versions[0], eng_data["sentences"])
    write_sentences(versions[1], fra_data["sentences"])


if __name__ == "__main__":
    main()
