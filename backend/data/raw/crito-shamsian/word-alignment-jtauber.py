#!/usr/bin/env python3

import csv
from pathlib import Path


input_path = Path("wegner-corrected-treebank.csv")


with input_path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader]


def get_base():
    filename = "../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-grc2b1.txt"

    for line in open(filename):
        ref, text = line.split(maxsplit=1)
        if ref == "54b.2.":
            continue
        tokens = list(enumerate(text.split(), 1))
        if tokens[0][1] in ["Σωκράτης.", "Κρίτων."]:
            tokens = tokens[1:]
        for idx, token in tokens:
            token = token.replace("\u1fbd", "\u2019")
            token = token.replace(":", "·")
            token = token.replace(",’", ",")
            token = token.replace(".’", ".")
            token = token.replace(";’", ";")
            token = token.lstrip("‘“")
            token = token.rstrip("”")
            if token.endswith((",", ";", ".", "·")):
                yield ref, idx, token[:-1]
                yield ref, idx, token[-1]
            else:
                yield ref, idx, token

i = 0
for ref, idx, token in get_base():
    print("@", ref, idx, token)
    row = rows[i]
    if row['word - form'] == "[0]":
        i += 1
        row = rows[i]
    if row['word - form'] == "[1]":
        i += 1
        row = rows[i]
    if row['word - form'] == "[2]":
        i += 1
        row = rows[i]
    if row['word - form'] == "[3]":
        i += 1
        row = rows[i]
    if row['word - form'] == "[4]":
        i += 1
        row = rows[i]
    # print(token, row['word - form'], row['sentence_id'], row['word - id'], ref, idx, i)
    print(ref, idx, i, sep="\t")
    if (row['sentence_id'], row['word - id']) in [
    ]:
        pass
    elif token != row['word - form']:
        break
    i += 1
