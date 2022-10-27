import csv
import json
import logging
import os
from collections import defaultdict
from pathlib import Path

import jsonlines
import yaml

from scaife_viewer.atlas.conf import settings
from scaife_viewer.atlas.models import (
    AttributionOrganization,
    AttributionPerson,
    AttributionRecord,
    GrammaticalEntry,
    GrammaticalEntryCollection,
    Node,
    TextAlignment,
    TextAlignmentRecord,
    TextAlignmentRecordRelation,
    TextAnnotation,
    TextAnnotationCollection,
    Token,
    TokenAnnotation,
)
from scaife_viewer.atlas.urn import URN
from scaife_viewer.atlas.utils import (
    get_lowest_citable_nodes,
    get_textparts_from_passage_reference,
)


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

    alignment = TextAlignment(
        label=data["label"],
        urn=data["urn"],
    )
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


def set_gorman_attributions(reset=False):
    person, created = AttributionPerson.objects.get_or_create(name="Vanessa Gorman")
    if not created or reset:
        # FIXME: Actually create the proper attribution modeling for this
        # TODO: Alias as records
        person.attributionrecord_set.all().delete()
    organization, _ = AttributionOrganization.objects.get_or_create(
        name="University of Nebraska-Lincoln"
    )

    syntax_trees = TextAnnotation.objects.filter(data__references__icontains="vgorman1")
    AttributionRecord.objects.create(
        person=person,
        organization=organization,
        role="Annotator",
        data=dict(references=[list(syntax_trees.values_list("urn"))]),
    )


def create_gorman_collection(reset=False):
    collection_urn = (
        "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:gorman_trees"
    )
    if reset:
        TextAnnotation.objects.filter(collection__urn=collection_urn).update(
            collection=None
        )
        TextAnnotationCollection.objects.filter(urn=collection_urn).delete()

    tas = TextAnnotation.objects.filter(data__references__icontains="vgorman1")
    collection = TextAnnotationCollection.objects.create(
        label="perseids-publications/gorman-trees",
        data={
            "source": {
                "title": "perseids-publications/gorman-trees",
                "url": "https://github.com/perseids-publications/gorman-trees",
            }
        },
        urn=collection_urn,
    )
    tas.update(collection=collection)


def set_glaux_attributions(reset=False):
    person, created = AttributionPerson.objects.get_or_create(name="Toon Van Hal")
    if not created or reset:
        # FIXME: Actually create the proper attribution modeling for this
        # TODO: Alias as records
        person.attributionrecord_set.all().delete()
    organization, _ = AttributionOrganization.objects.get_or_create(
        name="KU Leuven"
    )

    syntax_trees = TextAnnotation.objects.filter(urn__startswith="urn:cite2:beyond-translation:syntaxTree.atlas_v1:glaux-")
    AttributionRecord.objects.create(
        person=person,
        organization=organization,
        role="Annotator",
        data=dict(references=[list(syntax_trees.values_list("urn"))]),
    )


def create_glaux_collection(reset=False):
    collection_urn = (
        "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:glaux_trees"
    )
    if reset:
        TextAnnotation.objects.filter(collection__urn=collection_urn).update(
            collection=None
        )
        TextAnnotationCollection.objects.filter(urn=collection_urn).delete()

    tas = TextAnnotation.objects.filter(urn__startswith="urn:cite2:beyond-translation:syntaxTree.atlas_v1:glaux-")
    collection = TextAnnotationCollection.objects.create(
        label="gregorycrane/glaux-trees",
        data={
            "source": {
                "title": "gregorycrane/glaux-trees",
                "url": "https://github.com/gregorycrane/glaux-trees",
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
            idx=idx,
            alignment=ta,
            urn=f"{base_record_urn}_{idx}",
        )
        record.save()
        for version_obj, tokens in zip(versions, row):
            relation_obj = TextAlignmentRecordRelation(
                version=version_obj, record=record
            )
            relation_obj.save()
            relation_obj.tokens.set(tokens)


def add_iliad_english_persian_translations():
    collection_urn = "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:il_gregorycrane_gAGDT"
    limit = 492
    # TODO: Figure out why this query doesn't work as expected against
    # text_parts__urn relation
    trees = list(
        TextAnnotation.objects.filter(
            collection__urn=collection_urn,
            urn__startswith="urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-tlg0012-tlg001-"
            # text_parts__urn__startswith="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
        ).order_by("idx")[0:limit]
    )

    persian_text = list(
        get_textparts_from_passage_reference(
            "urn:cts:greekLit:tlg0012.tlg001.shamsian-far1:1.s1-1.s492",
            Node.objects.get(urn="urn:cts:greekLit:tlg0012.tlg001.shamsian-far1:"),
        )
    )
    english_text = list(
        get_textparts_from_passage_reference(
            "urn:cts:greekLit:tlg0012.tlg001.parrish-eng1-sentences:1.s1-1.s492",
            Node.objects.get(
                urn="urn:cts:greekLit:tlg0012.tlg001.parrish-eng1-sentences:"
            ),
        )
    )

    assert len(trees) == len(persian_text) == len(english_text)
    to_update = []
    for tree, persian, english in zip(trees, persian_text, english_text):
        tree.data["translations"] = [
            [english.text_content, "eng"],
            [persian.text_content, "far"],
        ]
        to_update.append(tree)
        TextAnnotation.objects.bulk_update(to_update, fields=["data"], batch_size=500)


def add_odyssey_english_translations():
    # TODO: Load Odyssey 5 from Parrish
    collection_urn = "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:il_gregorycrane_gAGDT"
    trees = TextAnnotation.objects.filter(
        collection__urn=collection_urn,
        urn__startswith="urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-tlg0012-tlg002-",
    )
    od_sentence_alignment = TextAlignment.objects.get(
        urn="urn:cite2:scaife-viewer:alignment.v1:odyssey-sentence-alignment-crane"
    )
    english_by_treebank_id = {}
    for record in od_sentence_alignment.records.all():
        sentence = record.metadata["items"][1][0][1]
        treebank_id = record.metadata["treebank_id"]
        english_by_treebank_id[treebank_id] = sentence

    to_update = []
    for tree in trees:
        treebank_id = tree.data["treebank_id"]
        english = english_by_treebank_id.get(treebank_id, "")
        tree.data["translations"] = [[english, "eng"]]
        to_update.append(tree)

    TextAnnotation.objects.bulk_update(to_update, fields=["data"], batch_size=500)


def add_additional_iliad_translations():
    collection_urn = "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:il_gregorycrane_gAGDT"
    limit = 492
    # TODO: Figure out why this query doesn't work as expected against
    # text_parts__urn relation
    trees = TextAnnotation.objects.filter(
        collection__urn=collection_urn,
        urn__startswith="urn:cite2:exploreHomer:syntaxTree.v1:syntaxTree-tlg0012-tlg001-",
    ).order_by("idx")[limit:]

    il_sentence_alignment = TextAlignment.objects.get(
        urn="urn:cite2:scaife-viewer:alignment.v1:iliad-sentence-alignment-crane"
    )
    english_by_treebank_id = {}
    for record in il_sentence_alignment.records.all():
        sentence = record.metadata["items"][1][0][1]
        treebank_id = record.metadata["treebank_id"]
        english_by_treebank_id[treebank_id] = sentence

    to_update = []
    for tree in trees:
        treebank_id = tree.data["treebank_id"]
        english = english_by_treebank_id.get(treebank_id, "")
        tree.data["translations"] = [[english, "eng"]]
        to_update.append(tree)

    TextAnnotation.objects.bulk_update(to_update, fields=["data"], batch_size=500)


def add_translations_to_trees(reset=None):
    # NOTE: Reset is a no-op
    add_iliad_english_persian_translations()
    add_additional_iliad_translations()

    add_odyssey_english_translations()


def add_glosses_to_trees(reset=None):
    # NOTE: Reset is a no-op
    collection_urn = "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:il_gregorycrane_gAGDT"
    # TODO: Figure out why this query doesn't work as expected against
    # text_parts__urn relation
    trees = TextAnnotation.objects.filter(
        collection__urn=collection_urn,
    ).order_by("idx")

    to_update = []
    for tree in trees:
        annotations = list(
            TokenAnnotation.objects.filter(token__text_part__in=tree.text_parts.all())
        )
        words = tree.data["words"]
        for word in words:
            annotation = next(
                iter(filter(lambda x: x.data["lemma"] == word["lemma"], annotations)),
                None,
            )
            if not annotation:
                annotation = next(
                    iter(
                        filter(
                            lambda x: x.data["word_value"] == word["value"], annotations
                        )
                    ),
                    None,
                )
                if not annotation:
                    if word.get("tag") == "u--------":
                        pass
                    elif word.get("value") in ["[0]", "[1]"]:
                        pass
                    elif word.get("ref"):
                        print(f'{word["ref"]}@{word["value"]}')
                    else:
                        print(f'{word["value"]}')
                    # ~40 words unmapped with this naive pass
            data = annotation.data if annotation else {}
            word.update(
                {
                    "glossEng": data.get("gloss (eng)", ""),
                    # TODO: Revisit Farnoosh's glosses for Od.
                    "glossFas": data.get("gloss (fas)", ""),
                }
            )
        to_update.append(tree)

    TextAnnotation.objects.bulk_update(to_update, fields=["data"], batch_size=500)


def import_grammatical_entries(reset=None):
    # FIXME: Add upstream on scaife-viewer/backend/atlas
    if reset:
        GrammaticalEntry.objects.all().delete()
        # TODO: Prefer "Grammar" and "GrammarAnnotation"?
        GrammaticalEntryCollection.objects.all().delete()
    # FIXME: Move to scaife-viewer/backend
    DIDAKTA_ROOT = Path("data/annotations/grammatical-entries/didakta")

    # Load metadata
    metadata_path = DIDAKTA_ROOT / "metadata.yml"
    collection_data = yaml.safe_load(metadata_path.open("rb"))
    # FIXME: Implement attribution modeling (entry, example, etc)
    collection = GrammaticalEntryCollection.objects.create(
        label=collection_data["label"],
        urn=collection_data["urn"],
        data=collection_data["metadata"]
    )

    # Load entries
    to_create = []
    jsonl_path = DIDAKTA_ROOT / "entries.jsonl"
    for row in jsonlines.Reader(jsonl_path.open("rb")):
        entry = GrammaticalEntry(
            collection=collection,
            urn=row["urn"],
            idx=row["idx"],
            label=row["label"],
            data=dict(
                title=row["data"]["title"],
                description=row["data"]["description"]
            )
        )
        to_create.append(entry)
    GrammaticalEntry.objects.bulk_create(to_create)

    # Load token annotations
    entry_lookup = {}
    for entry in GrammaticalEntry.objects.all():
        entry_lookup[entry.label] = entry

    # FIXME: Improve bulk loading of tokens
    # FIXME: Prefer subref over ve_ref
    tokens_lookup = defaultdict(list)
    csv_path = DIDAKTA_ROOT / "tokens.csv"
    reader = csv.DictReader(csv_path.open())
    for row in reader:
        tags = row["tags"].split(";")
        for tag in tags:
            entry = entry_lookup.get(tag)
            if entry:
                tokens_lookup[entry].append(row["ve_ref"])

    # FIXME: Support more than just Iliad
    tokens = Token.objects.filter(text_part__urn__startswith="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:")
    to_update = []
    for entry, token_ve_refs in tokens_lookup.items():
        tokens_qs = tokens.filter(ve_ref__in=token_ve_refs)
        to_update.append(
            (entry, tokens_qs)
        )

    for entry, tokens_qs in to_update:
        entry.tokens.set(tokens_qs)
