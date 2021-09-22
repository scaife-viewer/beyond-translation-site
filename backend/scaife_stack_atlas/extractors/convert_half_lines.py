import sys
from pathlib import Path


def extract_halflines(path):
    new_content = []
    with path.open() as f:
        for raw_line in f.readlines():
            ref, content = raw_line.split(" ", maxsplit=1)
            lines = [l.strip() for l in content.split("***") if l.strip()]
            for _lpos, line in enumerate(lines):
                line_pos = _lpos + 1
                half_lines = [hl.strip() for hl in line.split("###") if hl.strip()]
                for _hlpos, hl in enumerate(half_lines):
                    half_line_pos = _hlpos + 1
                    new_content.append(f"{ref}.{line_pos}.{half_line_pos} {hl}")
    return new_content


def main():
    path = Path(sys.argv[1])
    content = extract_halflines(path)

    new_path = Path(f"{path}".replace(".txt", "-hemis.txt"))
    with open(new_path, "w") as f:
        for l in content:
            f.write(f"{l}\n")


if __name__ == "__main__":
    main()
