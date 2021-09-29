import re
from collections import defaultdict
from pathlib import Path


def is_reference_range(line):
    """
    Checks to see if the line contains a reference range
    """
    return line[0].isdigit() and line[-1].isdigit() and len(line.split("-")) == 2


def persian_content(line):
    """
    Strip treebank IDs and return the Persian content.
    """
    # content = re.sub(r"[\d+][a-z]{0,1}", "", line)
    pieces = re.split(r"([\d]+[a-z]{0,1})", line)
    pieces = [p for p in pieces if p]
    odd = []
    even = []
    for pos, p in enumerate(pieces):
        if pos % 2 == 0:
            odd.append(p.strip())
        else:
            even.append(p.strip())
    return list(zip(odd, even))


def extract_refs_and_lines(input_path):
    """
    Extract passage references and content.
    """
    header = None
    by_refs_dict = defaultdict(list)
    with input_path.open(encoding="utf-8-sig") as f:
        for raw_line in f.readlines():
            line = raw_line.strip()
            if line and is_reference_range(line):
                header = line
            else:
                by_refs_dict[header].append(raw_line)
    return by_refs_dict


def write_text(output_path, refs_and_lines):
    """
    Write the text out to the ATLAS / text-server flat file format.
    """
    ref_to_sentence_id_map = {}
    with output_path.open("w") as f:
        chapter_counter = 1
        for ref, line_chunk in refs_and_lines.items():
            # TODO: Load books from input_path
            book_ref = "1"
            counter = 1
            for line in line_chunk:
                content = persian_content(line)
                for row_ref, row in content:
                    # NOTE: row_ref is the Treebank ID
                    final_ref = f"{book_ref}.{row_ref}"
                    print(" ".join([final_ref, row]), file=f)
                    counter += 1


def main():
    input_path = Path(
        "data/raw/homer-farnoosh/Farnoosh Homer without the line-breaks.txt"
    )
    refs_and_lines = extract_refs_and_lines(input_path)

    output_path = Path("data/library/tlg0012/tlg001/tlg0012.tlg001.shamsian-far1.txt")
    write_text(output_path, refs_and_lines)

if __name__ == "__main__":
    main()
