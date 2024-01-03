import sys
import time
from pathlib import Path

from lxml import html
from requests import Session


THROTTLE_DURATION = 0.1


def get_page_urls(client, base_url, url):
    resp = client.get(url)
    parsed = html.fromstring(resp.text)
    unique_pages = dict()
    pagination_links = parsed.xpath("//ul[@class='pagination']/li/a")
    end_link = None
    for link in pagination_links:
        is_end_link = link.text.startswith("End")
        if is_end_link:
            end_link = link
            continue
        href = link.attrib["href"]
        unique_pages[href] = None

    while True:
        next_url = f"{base_url}{href}"
        print(next_url)
        resp = client.get(next_url)
        time.sleep(THROTTLE_DURATION)
        parsed = html.fromstring(resp.text)
        pagination_links = parsed.xpath("//ul[@class='pagination']/li/a")
        for link in pagination_links:
            if link.text.startswith("End"):
                continue
            if link.text.endswith("Start"):
                continue
            href = link.attrib["href"]
            unique_pages[href] = None

        if href == end_link.attrib["href"]:
            break
    return unique_pages


def get_alignment_id_to_label_lookup(client, base_url, pages):
    alignment_id_to_label = dict()
    for href in pages:
        next_url = f"{base_url}{href}"
        print(next_url)
        resp = client.get(next_url)
        time.sleep(THROTTLE_DURATION)
        parsed = html.fromstring(resp.text)
        for alignment in parsed.xpath('//div[@class="ParallelSentence"]'):
            alignment_url = alignment.xpath("./h4/a")[0]
            label = alignment_url.text
            alignment_id = alignment_url.attrib["href"].split("id=")[1]
            alignment_id_to_label[alignment_id] = label
    return alignment_id_to_label


def download_alignment_html(url, outdir):
    client = Session()
    base_url = url.split("?")[0]
    pages = get_page_urls(client, base_url, url)
    id_to_label_lookup = get_alignment_id_to_label_lookup(client, base_url, pages)

    # NOTE: This is specific to Valeria Boano's dataset; should be refactored
    # further for additional datasets
    # delta = set(range(1, 559 + 1)).difference(
    #     set(sorted(int(i) for i in id_to_label_lookup.values()))
    # )
    # {377, 545}
    if url == "https://ugarit.ialigner.com/userProfile.php?userid=143818&tgid=14779":
        # add 545
        id_to_label_lookup["38755"] = "545"
        # only 377 is missing; either it is private or was not done by Valeria

    for alignment_id in id_to_label_lookup:
        outf = outdir / f"{alignment_id}.html"
        if outf.exists():
            continue
        print(f"fetching {outf}")
        detail_url = f"https://ugarit.ialigner.com/text.php?id={alignment_id}"
        resp = client.get(detail_url)
        time.sleep(THROTTLE_DURATION)
        outf.write_text(resp.text)


def main():
    """
    Usage:
    python scaife_stack_atlas/extractors/download_files_from_ugarit.py "https://ugarit.ialigner.com/userProfile.php?userid=143818&tgid=14779" data/raw/bellum-boano/ugarit
    """
    uagrit_alignment_url = sys.argv[1]
    outdir = Path(sys.argv[2])
    outdir.mkdir(exist_ok=True, parents=True)

    download_alignment_html(uagrit_alignment_url)


if __name__ == "__main__":
    main()
