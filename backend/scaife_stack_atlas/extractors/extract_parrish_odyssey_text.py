import json
import re
from pathlib import Path
from string import punctuation

from lxml import etree


SPLITTER = re.compile(r"(?P<inner>\[{1}[^\]]+\]{1})")
MOVE_PUNCTUATION = True


def extract_from_xml(input_path):
    with input_path.open() as f:
        tree = etree.parse(f)

    ns = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    matches = tree.xpath("//text:list-item", namespaces=ns)
    sentence_pattern = re.compile(r"\d{7}\w{0,1}")
    output_path = Path(str(input_path.absolute()).replace(".xml", ".txt"))
    with output_path.open("w") as outf:
        for pos, elem in enumerate(matches):
            content = " ".join([f.strip() for f in elem.itertext() if f.strip()])
            ref = f"5.{pos + 1}"
            words = []
            for word in content.split():
                if not word.strip():
                    continue
                if not sentence_pattern.match(word):
                    words.append(word)
            if ref.startswith("["):
                break
            print(ref, *words, file=outf)
    return output_path


def extract_pairs(input_path):
    pairs = []
    with input_path.open() as f:
        for line in f:
            ref, content = line.split(" ", maxsplit=1)

            found = SPLITTER.findall(content)
            iterable = SPLITTER.split(content)
            english = []
            greek = None
            records = []
            for word in iterable:
                if word.strip() not in found:
                    english_word = word.strip()
                    if (
                        MOVE_PUNCTUATION
                        and english_word
                        and english_word[0] in punctuation
                    ):
                        last_punc, english_word = english_word[0:1], english_word[1:]
                        english_word = english_word.strip()
                        try:
                            records[-1][1][-1] = f"{records[-1][1][-1]}{last_punc}"
                        except IndexError:
                            pairs[-1][-1][1][-1] = f"{pairs[-1][-1][1][-1]}{last_punc}"
                    english.append(english_word)
                    continue
                else:
                    greek = (
                        word.split("[", maxsplit=1)[1]
                        .rsplit(":", maxsplit=1)[-1]
                        .strip("]")
                        .split()
                    )
                    if next(iter(greek), "0") == "0":
                        # we need to ingest this stuff
                        greek = []
                    records.append((ref, english, greek))
                    # TODO: Uncomment the next line for debugging
                    # if len(greek) > 1:
                    #     print(line)
                    # else could retain greek if need be
                    # also need to check for unmapped english; equivalent of "0" for greek
                    english = []
            pairs.append(records)
    output_path = Path(str(input_path.absolute()).replace(".txt", "-pairs.json"))
    with output_path.open("w") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)
    return output_path


def write_english_text(input_path, output_path):
    pairs = json.load(input_path.open())
    with output_path.open("w") as outf:
        for pair in pairs:
            ref = f"{pair[0][0]}"
            print(ref, end=" ", file=outf)
            for fragment in pair:
                print(*fragment[1], end=" ", file=outf)
            print(file=outf)


def ensure_pairs(xml_path):
    text_path = extract_from_xml(xml_path)
    pairs_path = extract_pairs(text_path)

    # NOTE: We don't need the text path after we have pairs
    text_path.unlink()

    return pairs_path


def main():
    xml_path = Path("data/raw/homer-parrish/od-5-content.xml")
    pairs_path = ensure_pairs(xml_path)

    english_path = Path("data/library/tlg0012/tlg002/tlg0012.tlg002.parrish-eng1.txt")
    write_english_text(pairs_path, english_path)

    pairs_path.unlink()


if __name__ == "__main__":
    main()
