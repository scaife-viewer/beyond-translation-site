import csv
from pathlib import Path


def output_flat_text(column_name, output_path):
    input_path = Path("wegner-corrected-finalized-versions.csv")

    with input_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]

    with output_path.open("w") as output_file:
        for row in rows:
            ref = row["Title3"].rsplit("|", maxsplit=1)[1].split("Cr.")[1].strip(".").strip()
            if row[column_name].strip():
                print(f"{ref}. {row[column_name].strip()}", file=output_file)

output_flat_text("English", Path("../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-eng1.txt"))
output_flat_text("Benjamin Jowett", Path("../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-eng2.txt"))
output_flat_text("Schleiermacher", Path("../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-ger1.txt"))
output_flat_text("Primary translation", Path("../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-far1.txt"))
output_flat_text("Literal translation", Path("../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-far2.txt"))
output_flat_text("Secondary translation", Path("../../library/tlg0059/tlg003/tlg0059.tlg003.perseus-kur1.txt"))
