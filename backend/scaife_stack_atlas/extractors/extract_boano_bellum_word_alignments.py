"""
Usage: Paste the script into python manage.py shell
"""

import sys
from pathlib import Path

from scaife_stack_atlas.extractors.extract_alignments_from_ugarit_html import (
    extract_alignment_data,
    extract_records,
)
from scaife_stack_atlas.extractors.prepare_persian_alignments import (
    write_alignment_annotation,
)
from scaife_viewer.atlas.models import Token


LATIN_VERSION = "urn:cts:latinLit:phi0428.phi001.dll-ed-lat1:"
ENGLISH_VERSION = "urn:cts:latinLit:phi0428.phi001.dll-tr-eng1:"


def prepare_alignments(records, token_lookup, lat_tokens, eng_tokens):
    # TODO: Surface original record_id as the URN
    alignments = []
    for _, record in records:
        latin_relation = []
        eng_relation = []
        for side, token_ids in record.items():
            if side == "1":
                tokens = lat_tokens
                relation = latin_relation
                version = LATIN_VERSION
            else:
                tokens = eng_tokens
                relation = eng_relation
                version = ENGLISH_VERSION
            candidates = tokens[:]
            for token_id in token_ids:
                needle = token_lookup[token_id]
                print(needle)

                # FIXME: This will just return the first match; if a word is repeated, we will assign to the wrong identifier
                # fixed manually via https://github.com/scaife-viewer/beyond-translation-site/commit/676cff941c08dc2b41ba5fc2579c8f1fe8f47533
                haystack = next(
                    iter(filter(lambda x: x.word_value == needle, candidates)), None
                )
                if haystack:
                    print(haystack.ve_ref, haystack.word_value)
                    relation.append(f"{version}{haystack.ve_ref}")
                    # NOTE: This was one possible solution for improving the needle / haystack
                    # implementation
                    # candidates = [t for t in candidates if t.idx > haystack.idx]
                    # for candidate in candidates:
                    #     relation.append(candidate.ve_ref)
                else:
                    assert False
        alignments.append([latin_relation, eng_relation])
    return alignments


def extract_alignments(input_dir, limit=None):
    (
        alignment_lookup,
        citation_record_lookup,
        citation_stem_lookup,
        token_lookup,
    ) = extract_alignment_data(input_dir)

    records = extract_records(alignment_lookup, citation_record_lookup, limit)

    if limit != 1:
        raise NotImplementedError(
            "This script assumes we're working within the first citation of 1.1"
        )
    lat_tokens = list(
        Token.objects.filter(text_part__urn__startswith=LATIN_VERSION).filter(
            text_part__ref__in=["1.1"]
        )
    )
    eng_tokens = list(
        Token.objects.filter(text_part__urn__startswith=ENGLISH_VERSION).filter(
            text_part__ref__in=["1.1"]
        )
    )

    # uncomment to debug
    # from scaife_viewer_atlas.extractors.extract_alignments_from_ugarit_html import debug_records
    # debug_records(records, token_lookup, lat_tokens, eng_tokens)

    alignment_records = prepare_alignments(
        records, token_lookup, lat_tokens, eng_tokens
    )

    versions = [
        LATIN_VERSION,
        ENGLISH_VERSION,
    ]
    title = "De Bello Alexandrino Latin / English Word Alignment"
    alignment_urn = f"urn:cite2:scaife-viewer:alignment.v1:boano-balex-word-alignment"
    write_alignment_annotation(title, alignment_urn, versions, alignment_records)


def main():
    input_dir = Path("data/raw/bellum-boano/ugarit")
    limit = 1
    extract_alignments(input_dir, limit)

# Since this has Django imports, it is easier just to paste in the script to
# python manage.py shell and then run `main()`
