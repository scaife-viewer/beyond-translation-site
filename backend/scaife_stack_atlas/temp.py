import json
import logging
import os
from collections import defaultdict
from pathlib import Path

from scaife_viewer.atlas.conf import settings
from scaife_viewer.atlas.importers.token_annotations import apply_token_annotations
from scaife_viewer.atlas.models import (
    Node,
    TextAlignment,
    TextAlignmentRecord,
    TextAlignmentRecordRelation,
    TextAnnotation,
    TextAnnotationCollection,
    Token,
)
from scaife_viewer.atlas.urn import URN
from scaife_viewer.atlas.utils import get_lowest_citable_nodes, get_textparts_from_passage_reference


logger = logging.getLogger(__name__)


ANNOTATIONS_DATA_PATH = os.path.join(
    settings.SV_ATLAS_DATA_DIR, "annotations", "text-alignments"
)


def get_paths():
    if not os.path.exists(ANNOTATIONS_DATA_PATH):
        return []
    return [
        os.path.join(ANNOTATIONS_DATA_PATH, f)
        for f in os.listdir(ANNOTATIONS_DATA_PATH)
        if f.endswith(".json")
    ]


def process_file(path):
    data = json.load(open(path))

    versions = data["versions"]
    version_objs = []
    for version in versions:
        version_objs.append(Node.objects.get(urn=version))

    alignment = TextAlignment(label=data["label"], urn=data["urn"],)
    if data.get("enable_prototype"):
        alignment.metadata["enable_prototype"] = data["enable_prototype"]
    if data.get("display_options"):
        alignment.metadata["display_options"] = data["display_options"]

    alignment.save()
    alignment.versions.set(version_objs)

    idx = 0
    # TODO: review how we might make use of sort key from CEX
    # TODO: sorting versions from Ducat too, especially since Ducat doesn't have 'em
    # maybe something for CITE tools?
    for row in data["records"]:
        record = TextAlignmentRecord(
            idx=idx,
            alignment=alignment,
            urn=row["urn"],
            metadata=row.get("metadata", {}),
        )
        record.save()
        idx += 1
        for version_obj, relation in zip(version_objs, row["relations"]):
            relation_obj = TextAlignmentRecordRelation(
                version=version_obj, record=record
            )
            relation_obj.save()
            tokens = []
            # TODO: Can we build up a veref map and validate?
            for entry in relation:
                entry_urn = URN(entry)
                ref = entry_urn.passage
                # NOTE: this assumes we're always dealing with a tokenized exemplar, which
                # may not be the case
                text_part_ref, _ = ref.rsplit(".", maxsplit=1)
                text_part_urn = f"{version_obj.urn}{text_part_ref}"
                # TODO: compound Q objects query to minimize round trips
                tokens.append(
                    Token.objects.get(text_part__urn=text_part_urn, ve_ref=ref)
                )
            relation_obj.tokens.set(tokens)


def process_alignments(reset=False):
    if reset:
        TextAlignment.objects.all().delete()

    created_count = 0
    for path in get_paths():
        process_file(path)
        created_count += 1
    print(f"Alignments created: {created_count}")


def set_text_annotation_collection(reset=False):
    # TODO: Reset is a no-op
    collection_urn = "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:il_gregorycrane_gAGDT"
    if reset:
        TextAnnotation.objects.filter(collection__urn=collection_urn).update(
            collection=None
        )
        TextAnnotationCollection.objects.filter(urn=collection_urn).delete()

    tas = TextAnnotation.objects.filter(
        urn__istartswith="urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-tlg0012-"
    )
    collection = TextAnnotationCollection.objects.create(
        label="gregorycrane/gAGDT",
        data={
            "source": {
                "title": "gregorycrane/gAGDT",
                "url": "https://github.com/gregorycrane/gAGDT",
            }
        },
        urn=collection_urn,
    )
    tas.update(collection=collection)


# TODO: English too?
def create_persian_greek_alignment(reset=True):
    alignment_urn = (
        "urn:cite2:scaife-viewer:alignment.v1:iliad-greek-farsi-sentence-alignment"
    )
    if reset:
        TextAlignment.objects.filter(urn=alignment_urn).delete()
    path = Path(
        "data/annotations/text-alignments/iliad-greek-farsi-sentence-alignment.json"
    )
    process_file(path)
    ta = TextAlignment.objects.get(urn=alignment_urn)

    logger.info(f"Extracting tokens for {alignment_urn}")
    # NOTE: This assumes a whole lot of processing; eventually we want to make this a bit smarter
    record_lookup = defaultdict(list)
    versions = list(ta.versions.all())
    for version in versions:
        text_parts = get_lowest_citable_nodes(version)
        for idx, text_part in enumerate(text_parts):
            record_lookup[idx].append(text_part.tokens.all().only("id"))

    logger.info(f"Creating records for {alignment_urn}")
    base_record_urn = "urn:cite2:scaife-viewer:alignment-record.v1:iliad-greek-farsi-sentence-alignment"
    for idx, row in record_lookup.items():
        record = TextAlignmentRecord(
            idx=idx, alignment=ta, urn=f"{base_record_urn}_{idx}",
        )
        record.save()
        for version_obj, tokens in zip(versions, row):
            relation_obj = TextAlignmentRecordRelation(
                version=version_obj, record=record
            )
            relation_obj.save()
            relation_obj.tokens.set(tokens)


def add_translations_to_trees(reset=None):
    # NOTE: Reset is a no-op
    collection_urn = "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:il_gregorycrane_gAGDT"
    limit = 490
    # TODO: Figure out why this query doesn't work as expected against
    # text_parts__urn relation
    trees = list(TextAnnotation.objects.filter(
        collection__urn=collection_urn,
        urn__startswith="urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-tlg0012-tlg001-"
        # text_parts__urn__startswith="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
    ).order_by("idx")[0:limit])

    persian_text = get_textparts_from_passage_reference("urn:cts:greekLit:tlg0012.tlg001.shamsian-far1:1.s1-1.s490", Node.objects.get(urn="urn:cts:greekLit:tlg0012.tlg001.shamsian-far1:"))
    english_text = get_textparts_from_passage_reference("urn:cts:greekLit:tlg0012.tlg001.parrish-eng1-sentences:1.s1-1.s490", Node.objects.get(urn="urn:cts:greekLit:tlg0012.tlg001.parrish-eng1-sentences:"))

    to_update = []
    for tree, persian, english in zip(trees, persian_text, english_text):
        tree.data["translations"] = [
            [
                english.text_content,
                "eng"
            ],
            [
                persian.text_content,
                "far"
            ]
        ]
        to_update.append(tree)
    TextAnnotation.objects.bulk_update(to_update, fields=["data"], batch_size=500)
