import json
import re
from pathlib import Path

from tqdm import tqdm

from scaife_viewer.atlas.urn import URN  # noqa
from scaife_viewer.core.cts import collection, passage


BACKEND = Path(
    "/Users/jwegner/Data/development/repos/scaife-viewer/beyond-translation-site/backend"
)
COLLECTION_NAME = "glaux"


def write_text(output_path, refs_and_lines):
    """
    Write the text out to the ATLAS / text-server flat file format.
    """
    with output_path.open("w") as f:
        for row in refs_and_lines:
            print(" ".join(row), file=f)


def get_paths():
    syntax_trees_dir = BACKEND / "data/annotations/syntax-trees"
    return sorted(syntax_trees_dir.glob(f"{COLLECTION_NAME}_*"))


def ensure_tg_metadata_cts_backend(version_urn, tg_path, overwrite=False):
    metadata_path = Path(tg_path, "metadata.json")
    if overwrite or not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        tg_urn = version_urn.up_to(URN.TEXTGROUP)
        textgroup = collection(tg_urn[0:-1])
        data = {
            "urn": tg_urn,
            "node_kind": "textgroup",
            "name": [{"lang": "eng", "value": textgroup.label}],
        }
        with metadata_path.open("w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        assert False


def ensure_work_metadata_cts_backend(version_urn, w_path, overwrite=False):
    metadata_path = Path(w_path, "metadata.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not metadata_path.exists():
        version = collection(str(version_urn)[0:-1])
        work = list(version.ancestors())[-1]
        data = {
            "urn": version_urn.up_to(URN.WORK),
            "group_urn": version_urn.up_to(URN.TEXTGROUP),
            "node_kind": "work",
            "lang": work.metadata.lang,
            "title": [{"lang": "eng", "value": str(work.label)}],
            "versions": [
                {
                    "urn": str(version_urn),
                    "node_kind": "version",
                    "version_kind": "edition",
                    "lang": version.lang,
                    "first_passage_urn": f"{version_urn}{version.first_passage().reference}",
                    "citation_scheme": [c.name for c in version.metadata.citation],
                    "label": [
                        {
                            "lang": "eng",
                            "value": f"{version.label}",
                        }
                    ],
                    "description": [
                        {
                            "lang": "eng",
                            "value": re.sub(r"\s+", " ", version.description),
                        }
                    ],
                }
            ],
        }
        with metadata_path.open("w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        assert False


def stub_metadata(version_urn, overwrite=False):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]

    tg_path = BACKEND / f"data/library/{tgp}"
    ensure_tg_metadata_cts_backend(version_urn, tg_path, overwrite=overwrite)

    w_path = Path(tg_path, wp)
    ensure_work_metadata_cts_backend(version_urn, w_path, overwrite=overwrite)


def get_output_path(version_urn):
    tgp = version_urn.parsed["textgroup"]
    wp = version_urn.parsed["work"]
    vp = version_urn.parsed["version"]
    workpart_path = Path(BACKEND / f"data/library/{tgp}/{wp}")
    version_part = vp

    return Path(workpart_path, f"{tgp}.{wp}.{version_part}.txt")


def main(with_refs=True):
    # paths = get_paths()
    paths = [Path("/Users/jwegner/Data/development/repos/scaife-viewer/beyond-translation-site/backend/data/annotations/syntax-trees/glaux_syntax_trees_tlg0032.tlg005.perseus-grc2.json")]
    for path in paths:
        print(path.name)
        data = json.load(path.open())
        first_sentence = data[0]
        first_reference = next(iter(first_sentence["references"]), None)
        if not first_reference:
            msg = f"Could not resolve reference for {path.name}"
            print(msg)
            continue
        try:
            version_urn = URN(URN(first_reference).up_to(URN.VERSION))
            text = collection(version_urn.urn[:-1])
        except Exception:
            print(f"Could not load a version for {version_urn}")
            continue
        text_parts = []
        if with_refs:
            toc = text.toc()
            max_depth = len([cite for cite in toc.citations]) - 1
            refs = toc.depth_iter(max_depth)
            # FIXME: Could need a different depth detector
            # FIXME: Store these annotations elsewhere, no longer in
            # the project repo?
            # FIXME: ogl-pdl-annotations a third approach?
            for ref in tqdm(refs):
                passage_urn = f"{version_urn}{ref}"
                ref_passage = passage(passage_urn)
                text_content = "".join([t["w"] for t in ref_passage.tokenize()]).strip()
                text_content = re.sub(r"\s+", " ", text_content)
                text_parts.append((str(ref), text_content))
            if not text_parts:
                import ipdb

                ipdb.set_trace()
        # FIXME: Load from CTS resolver
        stub_metadata(version_urn, overwrite=True)
        if with_refs:
            output_path = get_output_path(version_urn)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_text(output_path, text_parts)


if __name__ == "__main__":
    main()
