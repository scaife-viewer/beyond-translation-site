from pathlib import Path
import json

from scaife_viewer.atlas.models import Node

version = Node.objects.get(urn="urn:cts:greekLit:tlg0012.tlg001.msA-folios:")
toc_entries = []
for folio in version.get_children():
    line = folio.get_descendants().filter(rank=3).first()
    folio_ref, book_line_ref = line.ref.split(".", maxsplit=1)
    toc_entries.append(
        {
            "title": f"{book_line_ref} :: {folio_ref}",
            "uri": f"urn:cts:greekLit:tlg0012.tlg001.msA-folios:{folio_ref}",
        }
    )

toc_path = Path("data/tocs/toc.iliad-folio-ref-1.json")
data = {
    "@id": "urn:cite:scaife-viewer:toc.iliad-folio-ref-1",
    "title": "Iliad Books by Folio Ref",
    "description": "Mapping between book / line boundaries to Venetus A folios",
    "items": toc_entries,
}
with toc_path.open("w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
