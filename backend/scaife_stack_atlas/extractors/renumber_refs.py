from pathlib import Path


def main():
    paths = [
        Path("data/library/tlg0012/tlg001/tlg0012.tlg001.shamsian-far1.txt"),
        Path("data/library/tlg0012/tlg001/tlg0012.tlg001.parrish-eng1-sentences.txt"),
        Path("data/library/tlg0012/tlg001/tlg0012.tlg001.perseus-grc1-sentences.txt"),
    ]
    for path in paths:
        lines = path.read_text().splitlines()

        renumbered = []
        for pos, line in enumerate(lines):
            _, content = line.split(" ", maxsplit=1)
            ref = f"1.s{pos + 1}"
            renumbered.append(f"{ref} {content}")
        path.write_text("\n".join(renumbered))


if __name__ == "__main__":
    main()
