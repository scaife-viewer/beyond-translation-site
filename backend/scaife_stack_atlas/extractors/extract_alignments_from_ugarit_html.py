from collections import defaultdict

from lxml import html


def extract_alignment_data(input_dir):
    alignment_lookup = dict()
    citation_stem_lookup = dict()
    citation_record_lookup = defaultdict(dict)
    token_lookup = dict()
    paths = input_dir.glob("*.html")
    paths = sorted(paths)
    for html_path in paths:
        parsed = html.parse(html_path.open())
        stem = html_path.stem
        for alignment in parsed.xpath(
            '//div[@class="ParallelSentence"]/*[@class="alignmentBlock"]'
        ):
            citation = alignment.xpath("../h4/a")[0].text
            citation_stem_lookup[citation] = stem
            for col in alignment.xpath('./*/*[@class="col-md-6"]'):
                col_id = col.attrib.get("id")
                if not col_id:
                    continue
                pos = col_id.split("_")[-1]
                tokens = col.xpath("./descendant::span")
                for token in tokens:
                    token_id = token.attrib["id"]
                    token_lookup[token_id] = token.text
                    alignment_id = token.attrib.get("data-ref")
                    if not alignment_id or alignment_id == "notAligned":
                        continue
                    alignment_lookup.setdefault(alignment_id, defaultdict(list))[
                        pos
                    ].append(token_id)
                    citation_record_lookup[citation][alignment_id] = None
    return alignment_lookup, citation_record_lookup, citation_stem_lookup, token_lookup


def extract_records(alignment_lookup, citation_record_lookup, limit=None):
    citations = list(citation_record_lookup.keys())[0:limit]
    records = []
    for citation in citations:
        for alignment_id in citation_record_lookup[citation]:
            records.append((alignment_id, alignment_lookup[alignment_id]))
    return records


def debug_records(records, token_lookup, lat_tokens, eng_tokens):
    for record_id, record in records:
        print(f"Record: {record_id}")
        print("Alignments:")
        for side, token_ids in record.items():
            if side == "1":
                tokens = lat_tokens
            else:
                tokens = eng_tokens
            text = []
            candidates = tokens[:]
            for token_id in token_ids:
                needle = token_lookup[token_id]
                haystack = next(
                    iter(filter(lambda x: x.word_value == needle, candidates)), None
                )
                if haystack:
                    print(haystack.ve_ref)
                    candidates = [t for t in candidates if t.idx > haystack.idx]
                text.append(token_lookup[token_id])
            value = f'\t{" ".join(text)}'
            print(value, end="")
            print()
        print()
