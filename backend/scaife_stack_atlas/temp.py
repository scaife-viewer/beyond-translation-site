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
    Dictionary,
    GrammaticalEntry,
    GrammaticalEntryCollection,
    ImageAnnotation,
    ImageROI,
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
    chunked_bulk_create,
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


def load_boano_metadata(reset=False):
    path = (
        Path(settings.SV_ATLAS_DATA_DIR)
        / "annotations/syntax-trees/bellum-boano/metadata.yml"
    )
    data = yaml.safe_load(path.read_text())
    collection_urn = data["urn"]

    # TODO: Reset is a no-op
    collection_urn = (
        "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:bellum_boano"
    )
    if reset:
        TextAnnotation.objects.filter(collection__urn=collection_urn).update(
            collection=None
        )
        TextAnnotationCollection.objects.filter(urn=collection_urn).delete()

    tas = TextAnnotation.objects.filter(
        urn__istartswith="urn:cite2:scaife-viewer:syntaxTree.v1:syntaxTree-phi0428-phi001-dll-ed-lat1"
    )
    collection = TextAnnotationCollection.objects.create(
        label="orcid.org/0009-0003-2791-1365",
        data={
            "source": data["source"],
            "fields": data["fields"],
        },
        urn=collection_urn,
    )
    tas.update(collection=collection)

    attribution_records = []
    for record in data.get("metadata", {}).get("attributions", []):
        person, _ = AttributionPerson.objects.get_or_create(name=record["name"])
        organization_data = record.get("organization")
        if organization_data:
            organization, _ = AttributionOrganization.objects.get_or_create(
                name=organization_data["name"]
            )
        attribution_records.append(
            AttributionRecord(
                person=person,
                organization=organization,
                role="Annotator",
                data=dict(references=[list(tas.values_list("urn"))]),
            )
        )
    AttributionRecord.objects.bulk_create(attribution_records)
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
    organization, _ = AttributionOrganization.objects.get_or_create(name="KU Leuven")

    syntax_trees = TextAnnotation.objects.filter(
        urn__startswith="urn:cite2:beyond-translation:syntaxTree.atlas_v1:glaux-"
    )
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

    tas = TextAnnotation.objects.filter(
        urn__startswith="urn:cite2:beyond-translation:syntaxTree.atlas_v1:glaux-"
    )
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


def add_glosses_to_trees(reset=None, debug=False):
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
                        if debug:
                            print(f'{word["ref"]}@{word["value"]}')
                    else:
                        if debug:
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


# FIXME: Refactor with add_glosses_to_trees
def add_anabasis_glosses_to_trees(reset=None, debug=False):
    # NOTE: Reset is a no-op
    text_annotation_collection_urn = (
        "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:glaux_trees"
    )
    version_urn = "urn:cts:greekLit:tlg0032.tlg006.perseus-grc2:"
    version = Node.objects.get(urn=version_urn)
    text_parts = get_lowest_citable_nodes(version)
    collection = TextAnnotationCollection.objects.get(
        urn=text_annotation_collection_urn
    )
    # TODO: Why is this subselect so slow?
    trees = collection.annotations.filter(
        text_parts__in=text_parts.values_list("id", flat=True)
    )

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
                        if debug:
                            print(f'{word["ref"]}@{word["value"]}')
                    else:
                        if debug:
                            print(f'{word["value"]}')
                    # ~40 words unmapped with this naive pass
            data = annotation.data if annotation else {}
            word.update(
                {
                    "glossEng": data.get("gloss (eng)", ""),
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
        data=collection_data["metadata"],
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
                title=row["data"]["title"], description=row["data"]["description"]
            ),
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
    tokens = Token.objects.filter(
        text_part__urn__startswith="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
    )
    to_update = []
    for entry, token_ve_refs in tokens_lookup.items():
        tokens_qs = tokens.filter(ve_ref__in=token_ve_refs)
        to_update.append((entry, tokens_qs))

    for entry, tokens_qs in to_update:
        entry.tokens.set(tokens_qs)


def stub_scholia_roi_to_token(reset=True):
    token = Token.objects.get(
        text_part__urn="urn:cts:greekLit:tlg0012.tlg001.msA-folios:12r.1.1", position=1
    )
    if reset:
        token.roi.all().delete()

    image_annotation = ImageAnnotation.objects.get(
        urn="urn:cite2:hmt:vaimg.2017a:VA012RN_0013"
    )
    roi = image_annotation.roi.filter(
        **{"data__urn:cite2:hmt:va_dse.v1.urn:": "urn:cite2:hmt:va_dse.v1:schol1"}
    ).first()
    if roi is None:
        roi = ImageROI(
            image_annotation=image_annotation,
            **{
                "data": {
                    "urn:cite2:hmt:va_dse.v1.urn:": "urn:cite2:hmt:va_dse.v1:schol1",
                    "urn:cite2:hmt:va_dse.v1.label:": "DSE record for scholion msA 1.2",
                    "urn:cite2:hmt:va_dse.v1.passage:": "urn:cts:greekLit:tlg5026.msA.hmt:1.2",
                    "urn:cite2:hmt:va_dse.v1.surface:": "urn:cite2:hmt:msA.v1:12r",
                    "urn:cite2:hmt:va_dse.v1.imageroi:": "urn:cite2:hmt:vaimg.2017a:VA012RN_0013@0.16265750,0.17631881,0.62733868,0.02494266",
                },
                "image_identifier": "https://image.library.jhu.edu/iiif/homer%2FVA%2FVA012RN-0013/",
                "coordinates_value": "0.16265750,0.17631881,0.62733868,0.02494266",
            },
        )
        roi.save()
        roi.text_parts.set([token.text_part])

    text_annotation = TextAnnotation.objects.filter(
        urn="urn:cts:greekLit:tlg5026.msA.hmt:1.2",
        data__references=["urn:cts:greekLit:tlg0012.tlg001.msA-folios:12r.1.1"],
    ).first()
    roi.text_annotations.set([text_annotation])
    roi.tokens.set([token])


# TODO: Consider this a candidate for upstream refactoring
def bulk_prepare_through_models(through_model, qs, lookup, from_field, to_field):
    logger.info("Preparing through objects for insert")
    to_create = []
    for urn, from_id in qs.values_list("urn", "pk"):
        to_ids = lookup[urn]
        for to_id in to_ids:
            to_create.append(through_model(**{from_field: from_id, to_field: to_id}))
    return to_create


# FIXME: Refactor this to an on-disk form; will require further changes to our
# data model and ingestion pipeline to fully support
def stub_scholia_roi_text_annotations(reset=True):
    collection_urn = (
        "urn:cite2:beyond-translation:text_annotation_collection.atlas_v1:hmt_scholia"
    )
    if reset:
        TextAnnotation.objects.filter(collection__urn=collection_urn).update(
            collection=None
        )
        TextAnnotationCollection.objects.filter(urn=collection_urn).delete()

    # create a collection and bind the second set of TAs to it
    version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA-folios:"
    version_obj = Node.objects.get(urn=version_urn)
    tas = TextAnnotation.objects.filter(text_parts__in=version_obj.get_descendants())
    collection = TextAnnotationCollection.objects.create(
        label="Scholia from the Homer Multitext project",
        data={
            "source": {
                "title": "homermultitext/hmt-archive",
                "url": "https://github.com/homermultitext/hmt-archive",
            }
        },
        urn=collection_urn,
    )
    tas.update(collection=collection)

    image_annotations = ImageAnnotation.objects.filter(
        text_parts__in=version_obj.get_descendants()
    )
    image_annotations_by_urn = {}
    for ia in image_annotations:
        image_annotations_by_urn[ia.urn] = ia

    rois_to_create = {}
    thru_text_annotations_lu = defaultdict(set)
    thru_text_parts_lu = defaultdict(set)
    for ta in tas:
        dse_data = ta.data["dse"]
        image_annotation_urn, coordinates = dse_data["image_roi"].split("@")

        try:
            ia = image_annotations_by_urn[image_annotation_urn]
        except KeyError:
            ia = ImageAnnotation.objects.filter(text_parts=ta.text_parts.first()).get()
            image_annotations_by_urn[image_annotation_urn] = ia
            # https://image.library.jhu.edu/iiif/homer%2FVA%2FVA083RN-0255/info.json exists
            # https://image.library.jhu.edu/iiif/homer%2FVA%2FVA083RN-0255/full/1500,1500/0/default.jpg
            # https://image.library.jhu.edu/iiif/homer%2FVA%2FVA083RN-0084/full/1500,1500/0/default.jpg
            # break
            # print(image_annotation_urn)
            # continue
        image_identifier = ia.image_identifier
        dse_urn = dse_data["urn"]
        roi = ImageROI(
            image_annotation=ia,
            image_identifier=image_identifier,
            coordinates_value=coordinates,
            urn=dse_urn,
        )

        rois_to_create.setdefault(dse_urn, roi)
        thru_text_annotations_lu[dse_urn].add(ta.id)
        thru_text_parts_lu[dse_urn].update(ta.text_parts.all().values_list("id", flat=True))

    ImageROI.objects.bulk_create(rois_to_create.values(), batch_size=500)
    qs = ImageROI.objects.filter(urn__in=rois_to_create.keys())

    ImageROIThroughTextPartsModel = ImageROI.text_parts.through
    prepared_objs = bulk_prepare_through_models(
        ImageROIThroughTextPartsModel, qs, thru_text_parts_lu, "imageroi_id", "node_id"
    )
    relation_label = ImageROIThroughTextPartsModel._meta.verbose_name_plural
    msg = f"Bulk creating {relation_label}"
    logger.info(msg)
    chunked_bulk_create(ImageROIThroughTextPartsModel, prepared_objs)

    ImageROIThroughTextAnnotationsModel = ImageROI.text_annotations.through
    prepared_objs = bulk_prepare_through_models(
        ImageROIThroughTextAnnotationsModel,
        qs,
        thru_text_annotations_lu,
        "imageroi_id",
        "textannotation_id",
    )
    relation_label = ImageROIThroughTextAnnotationsModel._meta.verbose_name_plural
    msg = f"Bulk creating {relation_label}"
    logger.info(msg)
    chunked_bulk_create(ImageROIThroughTextAnnotationsModel, prepared_objs)


def ingest_balex_extras(reset=True):
    # TODO: Update scaife-viewer-atlas package to support this use case;
    # we should resolve the XML from within a hint provided by metadata.json
    editions = [
        (
            "first-sibling",
            {
                "urn": "urn:cts:latinLit:phi0428.phi001.dll-conspectus-editionum-eng1:",
                "node_kind": "version",
                "version_kind": "commentary",
                "lang": "eng",
                "first_passage_urn": "urn:cts:latinLit:phi0428.phi001.dll-conspectus-editionum-eng1:all",
                "citation_scheme": ["content"],
                "label": [{"lang": "eng", "value": "Conspectus Editionum"}],
                "description": [{"lang": "eng", "value": "Cynthia Damon, et al."}],
            },
        ),
        (
            "first-sibling",
            {
                "urn": "urn:cts:latinLit:phi0428.phi001.dll-bibliography-eng1:",
                "node_kind": "version",
                "version_kind": "commentary",
                "lang": "eng",
                "first_passage_urn": "urn:cts:latinLit:phi0428.phi001.dll-bibliography-eng1:all",
                "citation_scheme": ["content"],
                "label": [{"lang": "eng", "value": "Bibliography"}],
                "description": [{"lang": "eng", "value": "Cynthia Damon, et al."}],
            },
        ),
        (
            "first-sibling",
            {
                "urn": "urn:cts:latinLit:phi0428.phi001.dll-preface-eng1:",
                "node_kind": "version",
                "version_kind": "commentary",
                "lang": "eng",
                "first_passage_urn": "urn:cts:latinLit:phi0428.phi001.dll-preface-eng1:all",
                "citation_scheme": ["content"],
                "label": [{"lang": "eng", "value": "Preface"}],
                "description": [{"lang": "eng", "value": "Cynthia Damon, et al."}],
            },
        ),
        (
            "last-sibling",
            {
                "urn": "urn:cts:latinLit:phi0428.phi001.dll-appendix-critica-eng1:",
                "node_kind": "version",
                "version_kind": "commentary",
                "lang": "eng",
                "first_passage_urn": "urn:cts:latinLit:phi0428.phi001.dll-appendix-critica-eng1:all",
                "citation_scheme": ["content"],
                "label": [{"lang": "eng", "value": "Appendix critica"}],
                "description": [{"lang": "eng", "value": "Cynthia Damon, et al."}],
            },
        ),
        (
            "last-sibling",
            {
                "urn": "urn:cts:latinLit:phi0428.phi001.dll-commentary-eng1:",
                "node_kind": "version",
                "version_kind": "commentary",
                "lang": "eng",
                "first_passage_urn": "urn:cts:latinLit:phi0428.phi001.dll-commentary-eng1:all",
                "citation_scheme": ["content"],
                "label": [{"lang": "eng", "value": "Studies on the Text"}],
                "description": [{"lang": "eng", "value": "Cynthia Damon, et al."}],
            },
        ),
    ]
    work_urn = URN("urn:cts:latinLit:phi0428.phi001:")
    work_node = Node.objects.get(urn=work_urn)
    version = (
        work_node.get_children()
        .filter(urn="urn:cts:latinLit:phi0428.phi001.dll-ed-lat1:")
        .first()
    )
    created = []
    # FIXME
    idx = 0
    for (position, edition) in editions:
        edition_urn = URN(edition["urn"])
        edition_kwargs = {
            "idx": idx,
            "kind": edition["node_kind"],
            "urn": edition["urn"],
            "metadata": {
                "citation_scheme": edition["citation_scheme"],
                "fallback_display_mode": True,
                "label": edition["label"][0]["value"],
                "lang": edition["lang"],
                "first_passage_urn": edition["first_passage_urn"],
                "description": edition["description"][0]["value"],
                "kind": edition["version_kind"],
            },
        }
        edition_node = version.add_sibling(position, **edition_kwargs)
        created.append(edition_node)
        # TODO: something in editions that keys up xml content
        xml_path = Path(
            f"data/library/phi0428/phi001/phi0428.phi001.{edition_urn.parsed['version']}.xml"
        )
        # TODO: Vendor assets within library?
        css_path = Path("data/raw/balex/balex-styles.scss")
        content = xml_path.read_text()
        textpart_kwargs = dict(
            kind="content",
            urn=f"{edition['urn']}all",
            ref="all",
            rank=1,
            # @@@ idx vs path for ranged queries; could derive IDX
            # from path as well
            idx=0,
            metadata=dict(content=content, css=css_path.read_text()),
        )
        edition_node.add_child(**textpart_kwargs)


def update_balex_metadata(reset=True):
    balex_work_obj = Node.objects.get(urn="urn:cts:latinLit:phi0428.phi001:")
    to_update = []
    for version in balex_work_obj.get_children():
        version.metadata.update(
            {
                "editor": {
                    "name": "Cynthia Damon, et al.",
                    "url": "http://viaf.org/viaf/116523553",
                },
                "repository": {
                    "name": "DigitalLatin/caesar-balex",
                    "url": "https://github.com/DigitalLatin/caesar-balex",
                },
            }
        )
        to_update.append(version)
    Node.objects.bulk_update(to_update, fields=["metadata"])


def add_cgl_css(reset=True):
    # NOTE: Reset is a no-op
    cgl = Dictionary.objects.get(
        urn="urn:cite2:scaife-viewer:dictionaries.v1:cambridge-greek-lexicon"
    )
    cgl.data["css"] = Path("data/raw/cambridge/lexicon.css").read_text()
    cgl.save()


def add_lexicon_thucydideum_css(reset=True):
    lexicon_thucydideum = Dictionary.objects.get(
        urn="urn:cite2:scaife-viewer:dictionaries.v1:lexicon-thucydideum"
    )
    lexicon_thucydideum.data["css"] = Path(
        "data/raw/lexicon-thucydideum/style.css"
    ).read_text()
    lexicon_thucydideum.save()
