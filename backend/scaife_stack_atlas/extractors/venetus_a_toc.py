from collections import defaultdict
from pathlib import Path
import json

from scaife_viewer.atlas.models import Node

version = Node.objects.get(urn="urn:cts:greekLit:tlg0012.tlg001.msA-folios:")
folios_by_book = defaultdict(list)
for folio in version.get_children():
    line = folio.get_descendants().filter(rank=3).first()
    folio_ref, book_line_ref = line.ref.split(".", maxsplit=1)
    book, line = book_line_ref.split(".")
    folios_by_book[book].append(
        {
            "title": f"{book_line_ref} :: {folio_ref}",
            "uri": f"urn:cts:greekLit:tlg0012.tlg001.msA-folios:{folio_ref}",
        }
    )

master_entries = []
for book, toc_entries in folios_by_book.items():
    urnish = f"toc.iliad-folio-ref-{book}"
    toc_path = Path(f"data/tocs/{urnish}.json")
    master_entries.append(
        {"title": f"{book}", "uri": f"urn:cite:scaife-viewer:{urnish}"}
    )
    root_entry = {
        "title": "↵",
        "uri": "urn:cite:scaife-viewer:toc.iliad-folio-ref-root",
    }
    data = {
        "@id": f"urn:cite:scaife-viewer:{urnish}",
        "title": f"Folio for Iliad Book {book}",
        "description": "Mapping between book / line boundaries to Venetus A folios",
        "items": [root_entry] + toc_entries,
    }
    with toc_path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

root_toc_path = Path("data/tocs/toc.iliad-folio-ref-root.json")
data = {
    "@id": "urn:cite:scaife-viewer:toc.iliad-folio-root",
    "title": "Iliad Books by Folio Ref",
    "description": "Mapping between book / line boundaries to Venetus A folios",
    "items": master_entries,
}
with root_toc_path.open("w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
