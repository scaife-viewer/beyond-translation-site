import csv
from pathlib import Path


# Fixed a ref at L209
input_path = Path("data/raw/crito-shamsian/wegner-corrected-finalized-versions.csv")

with input_path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader]

pos_to_ref_lookup = {}
for idx, row in enumerate(rows):
    pos = idx + 1
    ref = row["Title3"].rsplit("|", maxsplit=1)[1].split("Cr.")[1].strip(".").strip()
    pos_to_ref_lookup[str(pos)] = ref

assert len(pos_to_ref_lookup) == 268

edition_path = Path("data/library/tlg0059/tlg003/tlg0059.tlg003.perseus-grc2b1.txt")
translation_path = Path(
    "data/library/tlg0059/tlg003/tlg0059.tlg003.perseus-far1.txt",
)
for path in [edition_path, translation_path]:
    content = path.read_text().splitlines()
    with path.open("w") as f:
        for row in content:
            key, value = row.split(". ", maxsplit=1)
            ref = pos_to_ref_lookup[key]
            print(f"{ref}. {value}", file=f)
