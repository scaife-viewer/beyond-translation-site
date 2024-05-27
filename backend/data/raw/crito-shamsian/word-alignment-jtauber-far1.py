#!/usr/bin/env python3

from collections import defaultdict
import csv
from pathlib import Path


def cluster(pairs):
    clusters = []
    a_map = {}
    b_map = {}
    for a, b in pairs:
        if a not in a_map and b not in b_map:
            clusters.append([{a}, {b}])
            a_map[a] = len(clusters) - 1
            b_map[b] = len(clusters) - 1
        elif a in a_map and b not in b_map:
            clusters[a_map[a]][1].add(b)
            b_map[b] = a_map[a]
        elif a not in a_map and b in b_map:
            clusters[b_map[b]][0].add(a)
            a_map[a] = b_map[b]
    return clusters

d = defaultdict(lambda: defaultdict(list))
filename = "../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-far1.txt"

far_text = {}
for line in open(filename):
    ref, text = line.split(maxsplit=1)
    tokens = list(enumerate(text.split(), 1))
    far_text[ref] = "  ".join(b + "{" + str(a) + "}" for a, b in tokens)
    for idx, token in tokens:
        d[ref][token.strip("؟")].append(idx)

filename = "../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-grc2b1.txt"

grc_text = {}
for line in open(filename):
    ref, text = line.split(maxsplit=1)
    tokens = list(enumerate(text.split(), 1))
    grc_text[ref] = "  ".join(b + "{" + str(a) + "}" for a, b in tokens)


input_path = Path("wegner-corrected-treebank.csv")

with input_path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader]


# this is the human-readable output

prev = None
for line in open("map1.tsv"):
    ref, idx, line_num = line.strip().split()
    if prev is None or prev != ref:
        if prev is not None:
            for a, b in cluster(pairs):
                print("   ", a, b)
        print()
        print(ref)
        print("  ", grc_text[ref])
        print("  ", far_text[ref])
        print()
        pairs = set()
        prev = ref
    # print("@", ref, idx, line_num)
    for far_token in rows[int(line_num)]["Primary translation"].split():
        # print("#", far_token, d[ref][far_token])
        for far_idx in d[ref][far_token]:
            pairs.add((int(idx), far_idx))
for a, b in cluster(pairs):
    print("   ", a, b)

## this is the json-output

data = {}
data["urn"] = "urn:cite2:scaife-viewer:alignment.v1:crito-shamsian-word-alignment"
data["label"] = "Crito Greek / Farsi Word Alignment" 
data["format"] = "atlas-standoff-annotation"
data["enable_prototype"] = True
data["versions"] = ["urn:cts:greekLit:tlg0059.tlg003.perseus-grc2b1:", "urn:cts:greekLit:tlg0059.tlg003.perseus-far1:"]
data["records"] = []


def get_record_data():
    pairs = set()
    prev = None
    for line in open("map1.tsv"):
        ref, idx, line_num = line.strip().split()
        if prev is None or prev != ref:
            if prev is not None:
                for a, b in cluster(pairs):
                    yield(prev, a, b)
            pairs = set()
            prev = ref
        for far_token in rows[int(line_num)]["Primary translation"].split():
            for far_idx in d[ref][far_token]:
                pairs.add((int(idx), far_idx))
    for a, b in cluster(pairs):
        yield(ref, a, b)

idx = 0
for ref, a, b in get_record_data():
    relations1 = [
        f"urn:cts:greekLit:tlg0059.tlg003.perseus-grc2b1:{ref}t{i}" for i in a
    ]
    relations2 = [
        f"urn:cts:greekLit:tlg0059.tlg003.perseus-far1:{ref}t{i}" for i in b
    ]
    data["records"].append({
        "urn": f"urn:cite2:scaife-viewer:alignment-record.v1:crito-shamsian-word-alignment_{idx}",
        "relations": [relations1, relations2]
    })
    idx += 1


import json
json.dump(data, open("crito-shamsian-word-alignment.json", "w"), indent=2)
