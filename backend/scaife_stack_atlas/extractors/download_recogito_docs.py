import time
from pathlib import Path

import requests


def main():
    base_dir = Path("data/raw/homer-kemp/recogito_docs")
    base_dir.mkdir(parents=True, exist_ok=True)

    folder_content = requests.get(
        "https://recogito.pelagios.org/api/directory/chiara-p/f4075d34-41b9-433e-9a65-82a471526b7a"
    )

    s = requests.session()
    payload = {
        "username": "jacobwegner",
        "password": input("Provide your recogito password:\n"),
    }
    login_url = "https://recogito.pelagios.org/login"
    s.post(login_url, data=payload)

    folder_content = s.get(
        "https://recogito.pelagios.org/api/directory/chiara-p/f4075d34-41b9-433e-9a65-82a471526b7a"
    ).json()

    tei_export_url = (
        "https://recogito.pelagios.org/document/{document_id}/downloads/merged/tei"
    )
    for item in folder_content["items"]:
        url = tei_export_url.format(document_id=item["id"])
        version, passage = item["title"].rsplit(":", maxsplit=1)
        workpart = version.rsplit(":", maxsplit=1)[1]
        annotation_fname = f"{workpart}-{passage}-{item['id']}-tei.xml"
        r = s.get(url)
        annotation_path = Path(base_dir, annotation_fname)
        annotation_path.write_bytes(r.content)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
