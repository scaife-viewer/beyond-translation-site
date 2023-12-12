# TODO: Should this be in a pipeline or be done as part of preparation?
# This is basically a "virtual" alignment model, similar to SV1

# TODO: Also rework annotations down to the SEG level
# after we solve some display issues
import json
from pathlib import Path


def generate_body():
    return {
        "urn": "urn:cite2:scaife-viewer:alignment.v1:balex-alignment",
        "label": "Bellum Alexandrinum Alignment",
        "format": "atlas-standoff-annotation",
        "versions": [
            "urn:cts:latinLit:phi0428.phi001.dll-ed-lat1:",
            "urn:cts:latinLit:phi0428.phi001.dll-tr-eng1:",
        ],
        "records": [],
    }


def main():
    # TODO: Add attributions, additional metadata?
    body = generate_body()
    edition_path = Path("data/library/phi0428/phi001/phi0428.phi001.dll-ed-lat1.txt")
    translation_path = Path(
        "data/library/phi0428/phi001/phi0428.phi001.dll-tr-eng1.txt"
    )
    records = []
    edition_lu = {}
    for line in edition_path.read_text().splitlines():
        ref, content = line.split(" ", maxsplit=1)
        edition_lu[ref] = content

    translation_lu = {}
    for line in translation_path.read_text().splitlines():
        ref, content = line.split(" ", maxsplit=1)
        translation_lu[ref] = content

    for idx, ed_ref in enumerate(edition_lu):
        urn = f"urn:cite2:scaife-viewer:alignment-record.v1:balex-alignment_{idx}"
        edition_text = edition_lu[ed_ref]
        # NOTE: 3.3 was not translated
        tr_text = translation_lu.get(ed_ref, "")
        metadata = dict(
            label=ed_ref,
            items=[
                [[ed_ref, edition_text, "new"]],
                [[ed_ref, tr_text, None]],
            ],
        )
        # TODO: Determine if multiple relations make sense here so that we can access the
        # alignment from the "other" side.  This wasn't really possible with
        # the Iliad alignment, but should be revisited.
        relations = [[f"urn:cts:latinLit:phi0428.phi001.dll-ed-lat1:{ed_ref}.t1"], []]
        records.append(dict(urn=urn, metadata=metadata, relations=relations))
    body["records"] = records
    outf = Path("data/annotations/text-alignments/balex-tr-alignment.json")
    with outf.open("w") as f:
        json.dump(body, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
