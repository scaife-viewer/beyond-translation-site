import csv
import json
import uuid
from pathlib import Path


GREEK_VERSION = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
PERSIAN_VERSION = "urn:cts:greekLit:tlg0012.tlg001.shamsian-far1:"


def extract_alignments(input_path):
    """
    Extracts alignments from a CSV
    """
    rows = []
    with input_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    alignment_records = []
    for row in rows:
        has_greek = bool(row.get("greek_ve_ref"))
        has_persian = bool(row.get("persian_ve_ref"))
        if True not in set([has_greek, has_persian]):
            continue
        greek = [f'{GREEK_VERSION}{row["greek_ve_ref"]}']
        persian_refs = row["persian_ve_ref"].splitlines()
        persian = [f"{PERSIAN_VERSION}{ref}" for ref in persian_refs]
        alignment_records.append([greek, persian])
    # TODO: Manually handle greek 1.6.t4 being mapped twice.
    extra = alignment_records.pop(33)
    alignment_records[33][0].insert(0, extra[0][0])
    return alignment_records


def generate_alignment_urn(slug):
    """
    Generates a unique-ish URN for an alignment.
    """
    # TODO: Ensure unique URNs within scaife-viewer namespace
    minted_suffix = uuid.uuid4().hex
    return f"urn:cite2:scaife-viewer:alignment.v1:{slug}-{minted_suffix}"


def write_alignment_annotation(label, alignment_urn, versions, alignment_records):
    """
    Write out alignments to new format used in this project.

    # TODO: Backport extraction to scaife-viewer/backend
    """
    shared_urn_part = alignment_urn.rsplit(":", maxsplit=1)[1]
    data = dict(
        urn=alignment_urn,
        label=label,
        format="atlas-standoff-annotation",
        versions=versions,
        records=[],
    )
    idx = 0
    for record in alignment_records:
        record_urn = (
            f"urn:cite2:scaife-viewer:alignment-record.v1:{shared_urn_part}_{idx}"
        )
        data["records"].append(dict(urn=record_urn, relations=record,))
        idx += 1
    alignment_fname = f'{alignment_urn.rsplit(":", maxsplit=1)[1]}.json'
    # TODO: Handle mkdir

    alignments_dir = Path("data/annotations/text-alignments")
    alignments_dir.mkdir(parents=True, exist_ok=True)
    path = Path(alignments_dir, alignment_fname)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    input_path = Path(
        "data/raw/homer-farnoosh/Farnoosh Homer Persian Alignment - ve_refs_sample.csv"
    )

    alignment_records = extract_alignments(input_path)

    # alignment_urn = generate_alignment_urn("hafez-farsi-english-word-alignment")
    alignment_urn = "urn:cite2:scaife-viewer:alignment.v1:iliad-greek-farsi-word-alignment-32b47d02381146aeaf2eff5786e52400"
    versions = [
        GREEK_VERSION,
        PERSIAN_VERSION,
    ]
    title = "Iliad Greek / Farsi Word Alignment"
    write_alignment_annotation(title, alignment_urn, versions, alignment_records)


if __name__ == "__main__":
    main()
