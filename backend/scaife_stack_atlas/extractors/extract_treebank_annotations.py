"""
Script used to extract Odyssey treebank annotations
"""

import csv
import json
import unicodedata
from collections import Counter
from pathlib import Path

import regex

from scaife_stack_atlas.extractors.map_iliad_english_glosses import (
    build_eng_glosses_lookup,
)
from scaife_stack_atlas.postag_convert import deep_morphology_pos_and_parse
from scaife_viewer.atlas import tokenizers
from scaife_viewer.atlas.models import Node, Token


UNICODE_MARK_CATEGORY_REGEX = regex.compile(r"\p{M}")

ERROR_NO_REF_FOUND = "no ref found"
ERROR_INVALID_REF = "ref not valid"
ERRORS_NO_SUBREF_FOUND = "no subref found"
ERRORS = {ERROR_NO_REF_FOUND, ERROR_INVALID_REF, ERRORS_NO_SUBREF_FOUND}


def findall(p, s):
    """
    TODO: Use this to encode our subrefs off of tokens;
    if we need to handle partial matches we will have to
    resolve tokens differently in ATLAS anyways

    h/t https://stackoverflow.com/a/34445090
    """
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


def resolve_existing_token(version, text_part_ref, position):
    # NOTE: 1.95 is a bad ref
    return Token.objects.filter(
        text_part__urn=f"{version.urn}{text_part_ref}", position=position
    ).first()


def log_no_subref_error(text_part, word_value):
    if ERRORS_NO_SUBREF_FOUND in ERRORS:
        print(
            f"Could not retrieve {text_part.ref}@{word_value} from {text_part.text_content}"
        )


def heal_existing_token(existing_token, word_value):
    if existing_token.word_value == word_value:
        return False, existing_token

    if no_marks_normalized(word_value) == no_marks_normalized(
        existing_token.word_value
    ):
        return True, existing_token

    if existing_token.word_value.strip("ʼ") == word_value:
        # 1.3
        return True, existing_token

    if existing_token.word_value.startswith(word_value):
        # 1.59
        return True, existing_token

    prev_token = Token.objects.filter(
        text_part=existing_token.text_part, idx=existing_token.idx - 1
    ).first()
    if prev_token and prev_token.word_value.endswith(word_value):
        # 1.59
        # Skip; but revisit if we can resolve via subrefs
        return True, prev_token

    by_value = Token.objects.filter(
        text_part=existing_token.text_part, word_value=word_value
    ).first()
    if by_value:
        return True, by_value

    by_value_breathing = Token.objects.filter(
        text_part=existing_token.text_part, word_value=f"{word_value}ʼ"
    ).first()
    if by_value_breathing:
        return True, by_value_breathing

    by_partial_value_breathing = (
        f"{word_value}ʼ" in existing_token.text_part.text_content
    )
    if by_partial_value_breathing:
        # 5.43
        return False, None

    by_partial_value = word_value in existing_token.text_part.text_content
    if by_partial_value:
        # 5.32 has repeated split οὔτε
        # 5.212 οὐδὲ
        # 5.347 οὐδέ οὐδ
        # TODO: What is the appropriate thing here?
        return False, None

    # These are tokens we cannot resolve
    # TODO: Improve error output
    log_no_subref_error(existing_token.text_part, word_value)
    return False, None


def heal_token_by_word_value(version, text_part_ref, word_value):
    # NOTE: Retrieving only by word value
    text_part = Node.objects.filter(urn=f"{version.urn}{text_part_ref}").first()
    if not text_part:
        if ERRORS_NO_SUBREF_FOUND in ERRORS:
            print(f"Could not retrieve a text part for {text_part_ref}@{word_value}")
        return False, None
    token_by_value = text_part.tokens.filter(word_value=word_value).first()
    if token_by_value:
        return True, token_by_value

    token_by_value_with_breathing = text_part.tokens.filter(
        word_value=f"{word_value}ʼ"
    ).first()
    if token_by_value_with_breathing:
        return True, token_by_value_with_breathing

    # 5.347
    log_no_subref_error(text_part, word_value)
    return False, None


def no_marks_normalized(value):
    nfd_value = unicodedata.normalize("NFD", value)
    no_marks_value = UNICODE_MARK_CATEGORY_REGEX.sub("", nfd_value)
    nfkc_value = unicodedata.normalize("NFKC", no_marks_value)
    return nfkc_value.casefold()


def get_english_gloss(gloss_lookup, lemma):
    gloss = gloss_lookup.get(lemma, "")
    if not gloss:
        # TODO: Log fallback somewhere
        gloss = gloss_lookup.get(no_marks_normalized(lemma))
    return gloss


def sort_func(value):
    book, line, token = value.split(".")
    return (int(book), int(line), int(token.strip("t")))


def main():
    input_path = Path(
        "data/annotations/syntax-trees/gregorycrane_gagdt_syntax_trees_tlg0012.tlg002.perseus-grc2.json"
    )
    odyssey_annotations_path = Path(
        "data/annotations/token-annotations/od-crane/tlg0012.tlg002.perseus-grc2.csv"
    )

    fieldnames = [
        "ve_ref",
        "value",
        "word_value",
        "lemma",
        "part_of_speech",
        "gloss (eng)",
        "parse",
        "tag",
    ]
    annotations = []
    english_glosses = build_eng_glosses_lookup()
    refcounter = Counter()
    version = Node.objects.filter(
        urn__icontains="tlg0012.tlg002.perseus-grc2", depth=5
    ).first()
    # TODO: Resolve text parts and tokens down to CTS Refs?
    # Can we do it with the highlight-ish thing from SV 1, or do we need
    # fully implemented subreferences?  Is there prior art?
    with input_path.open() as f:
        data = json.load(f)
        for row in data:
            for w_idx, word in enumerate(row["words"]):
                annotation = dict()
                try:
                    ref = word["ref"]
                except KeyError:
                    if ERROR_NO_REF_FOUND in ERRORS:
                        print(
                            f"no ref found for {word['value']} [treebank_id=\"{row['treebank_id']}\"]"
                        )
                    continue
                try:
                    book, line = ref.split(".")
                except ValueError:
                    if ERROR_INVALID_REF in ERRORS:
                        print(
                            f"ref not valid {ref} [treebank_id=\"{row['treebank_id']}\"]"
                        )
                    continue

                # NOTE: Uncomment to debug a book at a time
                # if int(book) != 1:
                #     continue

                word_value = tokenizers.Token.get_word_value(word["value"])
                if not word_value:
                    continue

                # TODO: A bit of a code smell here
                refcounter[ref] += 1
                position = refcounter[ref]
                text_part_ref = f"{book}.{line}"
                annotation["ve_ref"] = f"{text_part_ref}.t{position}"
                annotation["word_value"] = word_value
                annotation["value"] = word["value"]
                annotation["lemma"] = word["lemma"]
                annotation["tag"] = word["tag"]
                (
                    annotation["part_of_speech"],
                    annotation["parse"],
                ) = deep_morphology_pos_and_parse(word["tag"])

                annotation["gloss (eng)"] = get_english_gloss(
                    english_glosses, word["lemma"]
                )

                existing_token = resolve_existing_token(
                    version, text_part_ref, position
                )
                if existing_token:
                    # TODO: make use of healed to log a correction;
                    # correction would need to resolve subref
                    healed, token = heal_existing_token(existing_token, word_value)
                else:
                    healed, token = heal_token_by_word_value(
                        version, text_part_ref, word_value
                    )

                if token:
                    annotation["ve_ref"] = token.ve_ref
                    # TODO: Also a code smell
                    refcounter[ref] = token.position
                    try:
                        if annotations[-1]["ve_ref"] != annotation["ve_ref"]:
                            annotations.append(annotation)
                    except IndexError:
                        annotations.append(annotation)

    annotations = sorted(annotations, key=lambda x: sort_func(x["ve_ref"]))
    with odyssey_annotations_path.open("w", encoding="utf-8-sig") as f:
        annotation_writer = csv.DictWriter(f, fieldnames=fieldnames,)
        annotation_writer.writeheader()
        annotation_writer.writerows(annotations)


if __name__ == "__main__":
    main()
