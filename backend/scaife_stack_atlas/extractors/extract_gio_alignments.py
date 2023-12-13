import csv
from pathlib import Path

import conllu

from scaife_stack_atlas.extractors.prepare_persian_alignments import (
    write_alignment_annotation,
)


GIO_DATA_DIR = Path(
    "/Users/jwegner/Data/development/repos/gregorycrane/gio-perseus-work-summer-2023"
)
# TODO: Djangoify
BASE_DATA_DIR = Path("data")

GREEK_VERSION = "urn:cts:greekLit:tlg2022.tlg007.gio-grc1:"
ENGLISH_VERSION = "urn:cts:greekLit:tlg2022.tlg007.gio-eng1:"

textgroup = {}
work = {}
version = {}


def check_bom(file_path):
    with open(file_path, "rb") as file:
        first_bytes = file.read(3)
    return first_bytes == b"\xef\xbb\xbf"


def load_data(text_path):
    encoding = "utf-8-sig" if check_bom(text_path) else "utf-8"
    return conllu.parse(text_path.read_text(encoding=encoding))


def write_text(output_path, refs_and_lines):
    """
    Write the text out to the ATLAS / text-server flat file format.
    """
    with output_path.open("w") as f:
        for row in refs_and_lines:
            print(" ".join(row), file=f)


def extract_english():
    input_path = Path(GIO_DATA_DIR / "Or 27_Eng_UD_Corr.conllx")
    data = load_data(input_path)

    refs_and_lines = []
    idx = 1
    for row in data:
        refs_and_lines.append([f"{idx}.", row.metadata["text"]])
        idx += 1

    output_path = BASE_DATA_DIR / "library/tlg2022/tlg007/tlg2022.tlg007.gio-eng1.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_text(output_path, refs_and_lines)


def extract_greek():
    input_path = Path(GIO_DATA_DIR / "Grc_UD_Corr.conllx")

    data = load_data(input_path)
    refs_and_lines = []
    idx = 1
    for row in data:
        refs_and_lines.append([f"{idx}.", row.metadata["text"]])
        idx += 1

    output_path = BASE_DATA_DIR / "library/tlg2022/tlg007/tlg2022.tlg007.gio-grc1.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_text(output_path, refs_and_lines)


def is_english_skippable(word):
    """
    This was done by manually comparing offsets in alignments/Gregory_Oration-27_Aligned_Corrected.csv
    to offsets in tokens_by_idx
    """
    if word["upos"] == "PUNCT":
        return True
    if word["upos"] == "PART" and word["xpos"] == "POS":
        return True
    if word["form"] == "’s":
        return True
    return False


def reverse_engineer_english():
    input_path = Path(GIO_DATA_DIR / "Or 27_Eng_UD_Corr.conllx")
    data = load_data(input_path)

    tokens_by_idx = {}
    idx = 0
    for sentence in data:
        for word in sentence:
            if is_english_skippable(word):
                continue
            tokens_by_idx[idx] = word
            idx += 1
    return tokens_by_idx


def is_greek_skippable(word):
    """
    This was done by manually comparing offsets in alignments/Gregory_Oration-27_Aligned_Corrected.csv
    to offsets in tokens_by_idx
    """
    if word["upos"] == "PUNCT":
        return True
    if word["deprel"] == "punct":
        return True
    if word["form"] in set(["—", "·", "ναντίον"]):
        return True
    return False


def reverse_engineer_greek():
    input_path = Path(GIO_DATA_DIR / "Grc_UD_Corr.conllx")
    data = load_data(input_path)

    tokens_by_idx = {}
    idx = 0
    for sentence in data:
        for word in sentence:
            if is_greek_skippable(word):
                continue
            tokens_by_idx[idx] = word
            idx += 1
    return tokens_by_idx


def skip_space_after(words, pos_0):
    this_word = words[pos_0]
    try:
        next_word = words[pos_0 + 1]
    except IndexError:
        return False
    return this_word["misc"]["end_char"] == next_word["misc"]["start_char"]


# TODO: Change the aligner notebook to work with consistent tokens / identifiers


def extract_english_tokens():
    fieldnames = ["value", "word_value", "space_after", "position", "ve_ref", "idx"]
    rows = []
    input_path = Path(GIO_DATA_DIR / "Or 27_Eng_UD_Corr.conllx")
    data = load_data(input_path)
    rows = []
    alignment_idx = 0
    idx = 0
    alignment_to_ve_ref_lookup = {}
    for sentence_pos, sentence in enumerate(data):
        ref = sentence_pos + 1
        for pos_0, word in enumerate(sentence):
            pos_1 = pos_0 + 1
            ve_ref = f"{ref}.t{pos_1}"
            rows.append(
                dict(
                    value=word["form"],
                    word_value=word["form"],
                    # skip_space_after, etc
                    space_after="false" if skip_space_after(sentence, pos_0) else "",
                    position=pos_1,
                    ve_ref=ve_ref,
                    idx=idx,
                )
            )
            idx += 1
            if is_english_skippable(word):
                continue
            else:
                alignment_to_ve_ref_lookup[alignment_idx] = ve_ref
                alignment_idx += 1

    output_path = BASE_DATA_DIR / "token-overrides/gio_eng_tokens.csv"
    with output_path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return alignment_to_ve_ref_lookup


def extract_greek_tokens():
    fieldnames = ["value", "word_value", "space_after", "position", "ve_ref", "idx"]
    rows = []
    input_path = Path(GIO_DATA_DIR / "Grc_UD_Corr.conllx")
    data = load_data(input_path)
    rows = []
    alignment_idx = 0
    idx = 0
    alignment_to_ve_ref_lookup = {}
    for sentence_pos, sentence in enumerate(data):
        ref = sentence_pos + 1
        for pos_0, word in enumerate(sentence):
            pos_1 = pos_0 + 1
            ve_ref = f"{ref}.t{pos_1}"
            rows.append(
                dict(
                    value=word["form"],
                    word_value=word["form"],
                    # skip_space_after, etc
                    space_after="false" if skip_space_after(sentence, pos_0) else "",
                    position=pos_1,
                    ve_ref=ve_ref,
                    idx=idx,
                )
            )
            idx += 1
            if is_greek_skippable(word):
                continue
            else:
                alignment_to_ve_ref_lookup[alignment_idx] = ve_ref
                alignment_idx += 1
    output_path = BASE_DATA_DIR / "token-overrides/gio_grc_tokens.csv"
    with output_path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return alignment_to_ve_ref_lookup


def extract_alignments(lookups):
    input_path = GIO_DATA_DIR / "Gregory_Oration-27_Aligned_Corrected.csv"
    alignment_records = []
    with input_path.open() as f:
        for pos, row in enumerate(csv.reader(f)):
            greek_idx = [pos]
            _, english = row[0], [col for col in row[1:] if col]
            english = [e for e in english]
            if english == ["0"]:
                english_idx = []
            else:
                english = [e.split(" ")[0].split("(")[1].split(",")[0] for e in english]
                english_idx = [int(e) for e in english]
            greek_ve_refs = [lookups["greek"][gidx] for gidx in greek_idx]
            english_ve_refs = [lookups["english"][eidx] for eidx in english_idx]
            greek_relation = [f"{GREEK_VERSION}{ve_ref}" for ve_ref in greek_ve_refs]
            english_relation = [f"{ENGLISH_VERSION}{ve_ref}" for ve_ref in english_ve_refs]
            alignment_records.append([greek_relation, english_relation])
    return alignment_records

    # From scaife_stack_atlas/extractors/prepare_persian_alignments.py


def main():
    extract_english()
    extract_greek()

    lookups = {
        "english": extract_english_tokens(),
        "greek": extract_greek_tokens(),
    }
    alignment_records = extract_alignments(lookups)

    versions = [
        GREEK_VERSION,
        ENGLISH_VERSION,
    ]
    title = "Gregory of Nyssa Greek / English Word Alignment"
    alignment_urn = (
        f"urn:cite2:scaife-viewer:alignment.v1:gio-gregory-nyssa-word-alignment"
    )
    write_alignment_annotation(title, alignment_urn, versions, alignment_records)


if __name__ == "__main__":
    main()

# remaining steps
# - [ ] populate library metadata
# - [x] extract flat text files
# - [x] create token files
# - [x] write alignment files
# - [ ] attribution records
