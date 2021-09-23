from pathlib import Path

import requests
from bs4 import BeautifulSoup


def fetch_html():
    response = requests.get("https://www.ccel.org/g/gibbon/decline/volume1/chap1.htm")
    html_string = response.text
    return BeautifulSoup(html_string, "html.parser")


def _s(int_val, padding=2):
    return f"{str(int_val).zfill(padding)}"


def generate_ref(chapter, section, paragraph):
    return f"{_s(chapter)}.{_s(section)}.{_s(paragraph)}"


def extract_textparts(html):
    chapter = 1
    section = 0
    paragraph = 0

    completed = []

    for p in html.find_all("p"):
        if p.attrs.get("class") == ["cite"]:
            completed.append(
                (
                    generate_ref(chapter, section, paragraph),
                    f"Chapter {chapter} :: {p.text}",
                )
            )
            continue
        if p.attrs.get("id"):
            section += 1
            paragraph = 0
            content = p.text.splitlines()
            title = content.pop(0)
            completed.append((generate_ref(chapter, section, paragraph), title))

            paragraph += 1
            content = [l.strip() for l in content]
            content = " ".join(content).strip()

            completed.append((generate_ref(chapter, section, paragraph), content))
        else:
            content = p.text.splitlines()
            content = [l.strip() for l in content]
            content = " ".join(content).strip()
            paragraph += 1
            completed.append((generate_ref(chapter, section, paragraph), content))
    return completed


def get_file_path(version_urn):
    workpart_part = version_urn.rsplit(":", maxsplit=2)[1]
    parts = workpart_part.split(".")[0:-1]
    work_dir = Path("data/library", *parts)
    work_dir.mkdir(exist_ok=True, parents=True)
    return Path(work_dir, f"{workpart_part}.txt")


def write_text_file(output_path, textparts):
    with output_path.open("w") as f:
        for part in textparts:
            print(" ".join(part), file=f)


def main():
    html = fetch_html()
    textparts = extract_textparts(html)

    version_urn = "urn:cts:engLit:gibbon.decline.ccel-eng1:"
    output_path = get_file_path(version_urn)
    write_text_file(output_path, textparts)


if __name__ == "__main__":
    main()
