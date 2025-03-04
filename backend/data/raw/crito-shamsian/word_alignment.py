# NOTE: This is a work in progress script; needs further refactoring to be promoted to an "extractor"
import csv
from collections import defaultdict
from pathlib import Path

from lxml import etree

from scaife_viewer.atlas.models import Node


# a CSV version of the treebank from Google Sheets
input_path = Path("data/raw/crito-shamsian/wegner-corrected-treebank.csv")


with input_path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader]


word_parts = defaultdict(list)

# The treebank does not have the speaker identification information;
# we would need some kind of heuristic to strip it out.
# This mapping goes from 1-based line offsets to CTS references
version = Node.objects.get(urn="urn:cts:greekLit:tlg0059.tlg003.perseus-grc2b1:")
textparts = version.get_descendants().filter(depth=7)
ref_lookup = {}
textpart_lookup = {}
for idx, t in enumerate(textparts):
    pos = str(idx + 1)
    ref_lookup[pos] = t.ref
    textpart_lookup[pos] = t

# All of the usual pitfalls here; we are trying to map strings in the treebank to
# whitespace separated tokens
# If possible, we should just map to the "Glaux" version (https://github.com/gregorycrane/glaux-trees/blob/master/public/xml/0059-003.xml)
# of the treebank and bring Farnoosh' annotations forward; need to do a diff and see what that actually looks like.
sentences = defaultdict(list)
ref_to_sentence_id_lookup = {}
for row in rows:
    _, sentence_id, word_id = row["word - ref"].rsplit("|", maxsplit=2)
    ref = ref_lookup[sentence_id]
    if sentence_id == "260":
        ref = ref_lookup["261"]
        # Sentence 260 is missing from the treebank, but we have the content in
        # the alignments, so we should just skip the identifier for our mapping purposes
    ref_to_sentence_id_lookup[ref] = sentence_id
    sentences[ref].append(row["word - form"])


# next functions are working towards word-level alignment and mapping Farnoosh's annotations to the glaux treebanks
skipped_forms = set(["[0]", "[1]", "[2]", "[3]", "[4]"])
# https://github.com/perseids-publications/pedalion-trees/blob/master/public/xml/crit.xml
old_treebank_path = Path("data/raw/crito-shamsian/crit.xml")
parsed = etree.parse(old_treebank_path.open())
old_sentence_counts = defaultdict(int)
for sentence in parsed.xpath("//sentence"):
    key = sentence.attrib["id"]
    for word in sentence.xpath("./word"):
        form = word.attrib["form"]
        if form in skipped_forms:
            continue
        old_sentence_counts[key] += 1

# from https://github.com/gregorycrane/glaux-trees/blob/master/public/xml/0059-003.xml
new_treebank_path = Path("data/raw/crito-shamsian/0059-003.xml")
parsed = etree.parse(new_treebank_path.open())
new_sentence_counts = defaultdict(int)
for sentence in parsed.xpath("//sentence"):
    key = sentence.attrib["id"]
    for word in sentence.xpath("./word"):
        form = word.attrib["form"]
        if form in skipped_forms:
            continue
        new_sentence_counts[key] += 1

# assert old_sentence_counts == new_sentence_counts
# Counts don't match; report on the differences

for old, new in zip(old_sentence_counts.items(), new_sentence_counts.items()):
    _, old_count = old
    _, new_count = new
    if new_count - old_count not in [2, 1, 0, -1, -2]:
        print(old, new)

# Try to map spreadsheet cells to tokens
sentences = defaultdict(list)
ref_to_sentence_id_lookup = {}
for row_pos, row in enumerate(rows):
    _, sentence_id, word_id = row["word - ref"].rsplit("|", maxsplit=2)
    ref = ref_lookup[sentence_id]
    if sentence_id == "260":
        ref = ref_lookup["261"]
        # Sentence 260 is missing from the treebank, but we have the content in
        # the alignments, so we should just skip the identifier for our mapping purposes
    ref_to_sentence_id_lookup[ref] = sentence_id
    sentences[ref].append(row["word - form"])
    ve_ref = f"{sentence_id}.t{word_id}"
    text_part = textpart_lookup[sentence_id]
    tokenish = text_part.text_content.split()
    needle = row["word - form"]
    if needle in set(["[0]"]):
        continue
    index_val = None
    try:
        index_val = tokenish.index(needle)
    except ValueError:
        for pos, token in enumerate(tokenish):
            if token.startswith(needle):
                index_val = pos
                break
    try:
        assert index_val is not None
    except AssertionError:
        for pos, token in enumerate(tokenish):
            if token.count(needle):
                index_val = pos
                break
    try:
        assert index_val is not None
    except AssertionError:
        print(f"Could not find index_val [row_pos={row_pos}]")
        continue
