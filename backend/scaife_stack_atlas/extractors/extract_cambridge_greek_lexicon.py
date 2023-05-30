import csv
import itertools
import json
from pathlib import Path

import jsonlines
from more_itertools import peekable


DICTIONARY_PATH = Path("data/annotations/dictionaries/cambridge-greek-lexicon")


def extract_entries():
    counters = dict(
        sense=0,
        entry=0,
        citation=0,
    )
    path = Path("data/raw/cambridge/all.tsv")
    reader = csv.reader(path.open(), delimiter="\t")
    for headword, content in reader:
        counters["entry"] += 1
        yield dict(
            headword=headword,
            data=dict(content=content),
            senses=[],
            citations=[],
            urn=f"urn:cite2:scafife-viewer:dictionary-entries.atlas_v1:cambridge-greek-lexicon-{counters['entry']}",
        )


def blob_entries():
    counter = 1
    entries = extract_entries()
    CHUNK_SIZE = 10000
    chunk = peekable(itertools.islice(entries, CHUNK_SIZE))
    entry_paths = []
    while chunk:
        entries_path = Path(DICTIONARY_PATH, f"entries-{str(counter).zfill(3)}.jsonl")
        print(counter)
        with entries_path.open("w") as f:
            writer = jsonlines.Writer(f)
            for entry in chunk:
                writer.write(entry)
        entry_paths.append(entries_path.name)
        counter += 1
        chunk = peekable(itertools.islice(entries, CHUNK_SIZE))
        if not chunk:
            break

    data = {
        # TODO: Label vs verbose label?
        "label": "Cambridge Greek Lexicon",
        "urn": "urn:cite2:scaife-viewer:dictionaries.v1:cambridge-greek-lexicon",
        "kind": "Dictionary",
        "entries": entry_paths,
    }
    metadata_path = Path(DICTIONARY_PATH, "metadata.json")
    with metadata_path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    DICTIONARY_PATH.mkdir(exist_ok=True, parents=True)
    blob_entries()


if __name__ == "__main__":
    main()
