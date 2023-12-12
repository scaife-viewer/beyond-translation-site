import csv
from pathlib import Path

from django.utils.functional import SimpleLazyObject

from scaife_viewer.atlas.language_utils import normalize_string


def build_eng_glosses_lookup():
    eng_glosses_path = Path("data/raw/homer-dik/shortdefsGreekEnglishLogeion.tsv")
    gloss_lu = {}
    gloss_reader = iter(
        csv.DictReader(eng_glosses_path.open(encoding="utf-8-sig"), delimiter="\t")
    )
    for row in gloss_reader:
        # lemma = normalize_string(row["lemma"])
        # # Store the normalized lemma form
        # gloss_lu[lemma] = row["def"]

        # Store the exact lemma form
        gloss_lu[row["lemma"]] = row["def"]
    return gloss_lu


def get_gloss(lemma):
    gloss = GLOSS_LU.get(lemma, None)
    if not gloss:
        # TODO: Work with @jtauber to determine a valid fallback path
        gloss = GLOSS_LU.get(normalize_string(lemma), "")
    return gloss


GLOSS_LU = SimpleLazyObject(build_eng_glosses_lookup)
