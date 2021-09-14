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
    content = re.sub(r"[\d+][a-z]{0,1}", "", line)
    return content.strip()


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
    with output_path.open("w") as f:
        for ref, lines in refs_and_lines.items():
            output_line = []
            output_line.append(f'1.{ref.split("-")[0]}')
            for line in lines:
                persian_line = persian_content(line)
                if persian_line:
                    output_line.append(persian_line)
            print(" ".join(output_line), file=f)


def main():
    input_path = Path(
        "data/raw/homer-farnoosh/Farnoosh Homer without the line-breaks.txt"
    )
    refs_and_lines = extract_refs_and_lines(input_path)

    output_path = Path("data/library/tlg0012.tlg001.shamsian-far1.txt")
    write_text(output_path, refs_and_lines)
