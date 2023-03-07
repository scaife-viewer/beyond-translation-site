import csv
import json
import logging
import pprint
import os
from functools import cache
from collections import Counter, defaultdict
from pathlib import Path
from scaife_viewer.atlas.urn import URN
from django.utils.functional import SimpleLazyObject

from thefuzz import process

# TODO: Vendor these out to ATLAS proper?
from scaife_stack_atlas.extractors.glosses import get_gloss
from scaife_stack_atlas.postag_convert import deep_morphology_pos_and_parse

# END TODO

from scaife_viewer.atlas.language_utils import normalize_string
from scaife_viewer.atlas.models import Token

OGL_PDL_ANNOTATIONS_ROOT = Path(
    os.environ.get(
        "OGL_PDL_ANNOTATIONS_ROOT",
        "/Users/jwegner/Data/development/repos/scaife-viewer/ogl-pdl-annotations",
    )
)
logger = logging.getLogger(__name__)
logger.setLevel = logging.INFO


def version_urn_to_fname(version_urn, extension="csv"):
    return f'{str(version_urn).split(":")[3]}.{extension}'


@cache
def build_fallback_lookup(urn):
    filename = version_urn_to_fname(urn, "tsv")
    source = (
        OGL_PDL_ANNOTATIONS_ROOT
        / f'data/token-annotations/{urn.parsed["textgroup"]}/{urn.parsed["work"]}/{filename}'
    )
    lookup = dict()
    # FIXME: 1.1.1@παῖδε[2] is wrong
    with source.open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            lookup[row["subref"]] = row["lemma"]
    return lookup


@cache
def build_treebank_lookups(version_urn):
    # we have to merge these words together here
    # TODO: Prefer JSONL format
    filename = version_urn_to_fname(version_urn, "json")
    treebank_path = Path(
        f'data/annotations/syntax-trees/glaux_syntax_trees_{filename}'
    )
    trees = json.load(treebank_path.open())
    tree_token_lookup = dict()
    forms_by_citation = defaultdict(Counter)
    for tree in trees:
        citation = tree["citation"].split(" ")[0]
        for word in tree["words"]:
            if word["relation"] == "PUNCT":
                continue
            form = word["value"]
            forms_by_citation[citation][form] += 1
            idx = forms_by_citation[citation][form]
            subref_value = f"{citation}@{form}"
            if idx > 1:
                subref_value = f"{subref_value}[{idx}]"
            tree_token_lookup[subref_value] = dict(lemma=word["lemma"], tag=word["tag"])
    return dict(
        tree_tokens=tree_token_lookup, forms_by_citation=forms_by_citation
    )


def fuzzy_token_match(fragment, candidates):
    """
    Performs a match using Levenshtein distance.

    Returns a match if the score returned by the matcher
    is greater than THRESHOLD.
    """
    THRESHOLD = 50
    choices = {}
    for c in candidates:
        choices[c] = normalize_string(c)

    # TODO: Tweak this match pattern
    # fragment_len = len(fragment)
    hits = process.extractBests(fragment, choices)
    for hit in hits:
        # if len(hit[0]) < fragment_len:
        #     continue
        # if hit[0].endswith("-"):
        #     continue
        if hit[1] > THRESHOLD:
            return hit[2]


def resolve_annotation(lookups, token, counters=None):
    if counters is None:
        counters = defaultdict(int)
    counters["total"] += 1
    ref = token.ve_ref.split(".t")[0]
    key = f"{ref}@{token.subref_value}"
    key = key.split("[1]")[0]
    if key in lookups["tree_tokens"]:
        return lookups["tree_tokens"][key]
    if key not in lookups["tree_tokens"]:
        try:
            first, second = key.strip("]").split("[")
        except Exception:
            first = key
            second = 1
        second = int(second) - 1
        off_by_one_key = f"{first}[{second}]"
        off_by_one_key = off_by_one_key.split("[1]")[0]
        if off_by_one_key in lookups["tree_tokens"]:
            counters["off_by_one"] += 1
            return lookups["tree_tokens"][off_by_one_key]
        elif off_by_one_key.split("[")[0] in lookups["tree_tokens"]:
            counters["raw_key"] += 1
            return lookups["tree_tokens"][off_by_one_key.split("[")[0]]
        elif key.replace("ʼ", "’") in lookups["tree_tokens"]:
            counters["appos"] += 1
            return lookups["tree_tokens"][key.replace("ʼ", "’")]
        else:
            citation = key.split("@")[0]
            if citation not in lookups["forms_by_citation"]:
                logger.warning(f"Citation not found {citation}")
                counters["no_citation"] += 1
                return None
            else:
                form_ref, form = key.split("@")
                normalized_form = normalize_string(form)
                partial_match = False
                for value in lookups["forms_by_citation"][citation]:
                    if normalize_string(value) in normalized_form:
                        partial_match = True
                        break
                if partial_match:
                    counters["partial"] += 1
                    repaired_key = f"{form_ref}@{value}"
                    logger.warning(f"Partial match attempt: {key}\t{repaired_key}")
                    # τἆλλα vs τ- ἆλλα
                    # return TREE_TOKEN_LU[repaired_key]

                    return None
                if fuzzy_token_match(normalized_form, lookups["forms_by_citation"][citation]):
                    fuzzy_match = fuzzy_token_match(
                        normalized_form, lookups["forms_by_citation"][citation]
                    )
                    repaired_key = f"{form_ref}@{fuzzy_match}"
                    counters["fuzzy"] += 1

                    logger.warning(f"Fuzzy match attempt: {key}\t{repaired_key}")
                    # return TREE_TOKEN_LU[repaired_key]
                    return None
                elif lookups["fallback"].get(key):
                    counters["fallback"] += 1
                    return dict(lemma=lookups["fallback"].get(key), tag="")
                else:
                    counters["missing"] += 1
                    logger.warning(f"Could not resolve {key}")
                    return None


def debug_subref_resolution(lookups, tokens):
    counters = dict(
        total=0,
        off_by_one=0,  # 816
        raw_key=0,  # 211
        appos=0,  # 1033
        no_citation=0,  # 19
        partial=0,  # 88
        fuzzy=0,  # 105
        fallback=0,  # 35
        missing=0,  # 9
    )

    for token in tokens:
        resolve_annotation(lookups, token, counters)
    # FIXME: info not being output
    # logger.info(pprint.pformat(counters))
    logger.warning(pprint.pformat(counters))


def write_glaux_annotations(lookups, version_urn, tokens):
    fieldnames = [
        "ve_ref",
        "value",
        "word_value",
        "lemma",
        "part_of_speech",
        "gloss (eng)",
        # NOTE: Not currently used
        # 'gloss (fas)',
        "parse",
        "tag",
    ]
    version_fname = version_urn_to_fname(version_urn)
    outf = Path(f"data/annotations/token-annotations/glaux/{version_fname}")
    outf.parent.mkdir(exist_ok=True, parents=True)
    with outf.open("w", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for token in tokens:
            row = defaultdict(None)
            row.update(
                dict(
                    ve_ref=token.ve_ref,
                    value=token.value,
                    word_value=token.word_value,
                )
            )

            data = resolve_annotation(lookups, token)
            if data:
                lemma = data["lemma"]
                if lemma:
                    row["lemma"] = lemma
                    row["gloss (eng)"] = get_gloss(lemma)

                tag = data["tag"]
                if tag:
                    # FIXME:
                    if tag == "b--------":
                        part_of_speech = ""
                        parse = "INDECL"
                    else:
                        part_of_speech, parse = deep_morphology_pos_and_parse(tag)
                    row.update(
                        dict(tag=tag, part_of_speech=part_of_speech, parse=parse)
                    )
            writer.writerow(row)


def get_lookups(version_urn):
    lookups = dict(
        fallback=build_fallback_lookup(version_urn),
        **build_treebank_lookups(version_urn)
    )
    return lookups


def main():
    version_urns = ["urn:cts:greekLit:tlg0032.tlg006.perseus-grc2:"]
    for urn_ in version_urns:
        version_urn = URN(urn_)
        tokens = Token.objects.filter(text_part__urn__startswith=version_urn)
        lookups = get_lookups(version_urn)
        # TODO: Uncomment this line to debug
        # debug_subref_resolution(lookups, tokens)
        write_glaux_annotations(lookups, version_urn, tokens)


if __name__ == "__main__":
    main()
