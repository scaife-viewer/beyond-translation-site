# NOTE: Breadcrumb of a script to convert from CSV to YAML for entities.
# Standoff annotations stay the same
# Paths change to support scaife-viewer-atlas changes

# Step 1: Create collections for the Odyssey and Iliad entities
# Step 2: Use objects.bulk_update to set the existing entities to their collections
# Step 3: Iterate through the collections and dump them out to YAML
# Step 4: Add annotator information (see later work in 570572ac)
# `metadata.attributions`

from pathlib import Path

import yaml

from scaife_viewer.atlas.models import NamedEntityCollection


def main():
    for collection in NamedEntityCollection.objects.all():
        data = dict(label=collection.label, urn=collection.urn, entities=[])
        for entity in collection.entities.all():
            data["entities"].append(
                dict(
                    title=entity.title,
                    description=entity.description,
                    kind=entity.kind,
                    url=entity.url,
                    data=entity.data,
                    urn=entity.urn,
                )
            )
        output_path = Path("path-to-dest.yml")
        yaml.safe_dump(data, output_path.open("w"), allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    main()
