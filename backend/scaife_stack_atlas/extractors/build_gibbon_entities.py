# We have extracted the name and the Plieades data into a lookup file
import csv
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import requests
import yaml


def load_entities(input_path, version_urn):
    from scaife_viewer.atlas.models import Token

    entities = json.load(input_path.open())
    # TODO: MOre precision?
    tokens = Token.objects.filter(text_part__urn__startswith=version_urn)

    token_lookup = defaultdict(list)
    for entity in entities:
        for part in entity.split():
            found = tokens.filter(word_value=Token.get_word_value(part))
            for token in found:
                token_lookup[token.ve_ref].append(entity)

    return (entities, token_lookup)


def fetch_pleiades_data(entities):
    s = requests.Session()
    entities_with_data = {}
    for entity, pid in entities.items():
        print(entity)
        data = s.get(f"https://pleiades.stoa.org{pid}/json").json()
        if not data["reprPoint"]:
            continue
        time.sleep(0.25)
        entities_with_data[entity] = dict(
            title=data["title"],
            description=data["description"],
            coordinates=", ".join([str(p) for p in data["reprPoint"]]),
        )
    return entities_with_data


def build_collection(entities, pleiades_data):
    sorted_entities = sorted(pleiades_data.keys())
    idx = 0
    collection = dict(
        label="Places from Gibbon Chapter 1",
        urn="urn:cite2:beyond-translation:named_entity_collection.atlas_v1:gibbon_1_places",
        metadata=dict(attributions=[dict(name="Peter Nadel", role="Annotator")]),
        entities=[],
    )

    urn_lookup = {}
    base_urn = "urn:cite2:beyond-translation:place.atlas_v1:"
    for key in sorted_entities:
        input_entity = pleiades_data[key]
        urn = f"{base_urn}{idx}"
        collection["entities"].append(
            dict(
                title=input_entity["title"],
                description=input_entity["description"],
                kind="place",
                url=f"https://pleiades.stoa.org{entities[key]}",
                data=dict(coordinates=input_entity["coordinates"],),
                urn=urn,
            )
        )
        urn_lookup[key] = urn
        idx += 1
    return (collection, urn_lookup)


def write_collection(output_path, collection):
    with output_path.open("w") as f:
        # TODO: Sort consistently
        yaml.safe_dump(collection, f)


def build_standoff_annotations(version_urn, token_lookup, urn_lookup):
    rows = []
    for token, entity_strs in token_lookup.items():
        for entity in entity_strs:
            try:
                entity_urn = urn_lookup[entity]
            except KeyError:
                continue
            else:
                ref, position = token.rsplit(".t")
                passage_urn = f"{version_urn}{ref}"
                rows.append([entity_urn, passage_urn, position])
    return rows


def write_standoff_annotations(output_path, rows):
    with output_path.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["named_entity_urn", "ref", "token_position"])
        for row in rows:
            writer.writerow(row)


def main():
    input_path = Path("data/raw/gibbon-nadel/chap1_places.json")
    version_urn = "urn:cts:engLit:gibbon.decline.ccel-eng1:"

    entities, token_lookup = load_entities(input_path, version_urn)
    pleiades_data = fetch_pleiades_data(entities)

    collection, urn_lookup = build_collection(entities, pleiades_data)

    collection_path = Path(
        "data/annotations/named-entities/processed/collections/gibbon_ch1_places.yml"
    )
    write_collection(collection_path, collection)

    standoff_rows = build_standoff_annotations(version_urn, token_lookup, urn_lookup)

    standoff_path = Path(
        "data/annotations/named-entities/processed/standoff/gibbon_ch1_places.csv"
    )

    write_standoff_annotations(standoff_path, standoff_rows)


if __name__ == "__main__":
    main()
