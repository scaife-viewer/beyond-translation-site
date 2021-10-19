import json
import os
import re
from collections import Counter
from pathlib import Path
from string import digits

import django


# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()


from django.db.models import Q

from scaife_viewer.atlas.models import (
    Node,
    TextAlignment,
    TextAlignmentRecord,
    TextAlignmentRecordRelation,
    Token,
)

from scaife_stack_atlas.extractors.extract_parrish_odyssey_text import ensure_pairs





def resolve_pairs(pairs, greek_version):
    """
    This should be done after running `prepare_db`
    """
    new_pairs = []
    for pair in pairs:
        new_pair = []

        token_counter = Counter()
        ref = pair[0][0]
        greek_tokens = Token.objects.filter(text_part__urn=f"{greek_version.urn}{ref}")
        position = 1
        for record in pair:
            greek_ve_refs = []
            for tv in record[2]:
                tw = Token.get_word_value(tv)
                non_numeric_tw = re.compile(r"\d").sub("", tw)
                relevant = list(
                    greek_tokens.filter(
                        Q(word_value=tw)
                        | Q(word_value=f"{tw}ʼ")
                        | Q(word_value=non_numeric_tw)
                    )
                )
                if not relevant:
                    # NOTE: These could be things where the sentence boundaries from treebank
                    # are useful; skip for now
                    # if tw and tw not in ["ἀντιάσας", "κέν", "πάντων", "ἐν", "ἑοῖσι", "στήθεσσιν", "οὐ", "δ"]:
                    #     assert False
                    # else:
                    #     continue
                    greek_ve_refs.append(None)
                    continue

                token = None
                if len(relevant) == 1:
                    token = relevant[0]
                else:
                    # repeated words
                    key = relevant[0].word_value
                    if key not in token_counter:
                        token_counter[key] = 0
                    try:
                        token = relevant[token_counter[key]]
                    except IndexError:
                        if tv[-1] in digits:
                            print(f"possible bug in {ref}")
                            offset = int(tv[-1]) - 1
                            token = relevant[offset]
                    token_counter[key] += 1
                greek_ve_refs.append(token.ve_ref)

            eng_ve_refs = []
            for word in record[1]:
                for possible_word in word.split():
                    w = possible_word.strip()
                    if w:
                        eng_ve_refs.append(f"{ref}.t{position}")
                        position += 1
            new_record = [eng_ve_refs, greek_ve_refs]
            new_pair.append(new_record)
        new_pairs.append(new_pair)
    return new_pairs


def create_alignment_records(new_pairs, greek_version, english_version):
    alignment_urn = "urn:cite2:scaife-viewer:alignment.v1:odyssey-word-alignment-parrish-998078bc3bab42978b47fa8e8b852cae"
    ta = TextAlignment.objects.create(
        label="Odyssey Word Alignment",
        urn=alignment_urn,
        # format="atlas-standoff-annotation",
    )
    ta.versions.set([english_version, greek_version])
    alignment = ta

    version_objs = [english_version, greek_version]

    idx = 0
    shared_urn_part = alignment_urn.rsplit(":", maxsplit=1)[1]
    for pair in new_pairs:
        for entry in pair:
            urn = f"urn:cite2:scaife-viewer:alignment-record.v1:{shared_urn_part}_{idx}"
            record = TextAlignmentRecord(idx=idx, alignment=alignment, urn=urn)
            record.save()
            idx += 1

            # stop at 2pm
            for version_obj, relation in zip(version_objs, entry):
                relation_obj = TextAlignmentRecordRelation(
                    version=version_obj, record=record
                )
                relation_obj.save()

                tokens = []
                for ve_ref in [r for r in relation if r]:
                    if not relation:
                        # @@@
                        continue
                    if version_obj == english_version:
                        text_part_ref, position = ve_ref.rsplit(".t", maxsplit=1)
                    else:
                        text_part_ref, position = ve_ref.rsplit(".t", maxsplit=1)
                        if position.startswith("t"):
                            position = position[1:]

                    text_part_urn = f"{version_obj.urn}{text_part_ref}"
                    # TODO: compound Q objects query to minimize round trips
                    tokens.append(
                        Token.objects.get(
                            text_part__urn=text_part_urn, position=position
                        )
                    )
                relation_obj.tokens.set(tokens)
    return ta


# FIXME: This performance is pretty stinking slow
def get_raw_records(records):
    raw_records = []
    for record in records:
        raw_relations = []
        for relation in record.relations.all():
            raw_relation = []
            for token in relation.tokens.all().select_related("text_part"):
                version_urn = f'{token.text_part.urn.rsplit(":", maxsplit=1)[0]}:'
                raw_relation.append(f"{version_urn}{token.ve_ref}")
            raw_relations.append(raw_relation)
        raw_records.append({"urn": record.urn, "relations": raw_relations})
    return raw_records


def get_data(text_alignment):
    return {
        "urn": text_alignment.urn,
        "label": text_alignment.label,
        "format": "atlas-standoff-annotation",
        "versions": [v.urn for v in text_alignment.versions.all()],
        "records": get_raw_records(text_alignment.records.all()),
    }


def main():
    xml_path = Path("data/raw/homer-parrish/od-5-content.xml")
    pairs_path = ensure_pairs(xml_path)

    input_path = Path("data/raw/homer-parrish/od-5-content-pairs.json")
    pairs = json.load(input_path.open())
    greek_version = Node.objects.get(
        urn="urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:"
    )
    alignment_pairs = resolve_pairs(pairs, greek_version)

    alignment_pairs_path = Path("data/raw/homer-parrish/od-5-alignment-pairs.json")
    with alignment_pairs_path.open("w") as f:
        json.dump(alignment_pairs, f, indent=2, ensure_ascii=False)

    english_version = Node.objects.get(
        urn="urn:cts:greekLit:tlg0012.tlg002.parrish-eng1:"
    )
    # text_alignment = create_alignment_records(
    #     alignment_pairs, greek_version, english_version
    # )

    # alignment_output_path = Path(
    #     "data/annotations/text-alignments/odyssey-word-alignment-parrish-998078bc3bab42978b47fa8e8b852cae.json"
    # )

    # data = get_data(text_alignment)
    # with alignment_output_path.open("w") as f:
    #     json.dump(data, f, ensure_ascii=False, indent=2)
