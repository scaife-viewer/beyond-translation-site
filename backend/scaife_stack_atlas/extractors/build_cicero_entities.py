import csv
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import django

import requests
import yaml


# TODO: refactor this as an actual Django management command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()


def build_entities_lookup(input_path, version_urn):
    lookup = {}
    with input_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_name = row["location"]
            if not entity_name:
                continue
            coordinates = ", ".join(
                [
                    coord
                    for coord in [row["location_lat"], row["location_long"]]
                    if coord.strip()
                ]
            )
            entity = lookup.setdefault(
                entity_name,
                {
                    "title": entity_name,
                    "description": "",
                    "kind": "place",
                    "data": {"coordinates": coordinates},
                    "url": "",
                    "pseudo_references": [],
                },
            )
            letter_urn = f'{version_urn}{row["book"]}.{row["letter"]}'

            entity["pseudo_references"].append(
                (
                    # NOTE: Split ensures we handle multi-token
                    # selections
                    letter_urn,
                    row["selection"].split(),
                )
            )
    return lookup


def build_token_lookup(entities_lookup):
    # TODO: Make the entity key a unique URN
    from scaife_viewer.atlas.models import Token

    token_lookup = defaultdict(list)
    for entity, data in entities_lookup.items():
        pseudo_refs = data.pop("pseudo_references")
        for (letter_urn, values) in pseudo_refs:
            tokens = Token.objects.filter(text_part__urn__startswith=f"{letter_urn}.")
            # tokens = Token.objects.filter(text_part__urn__startswith="urn:cts:latinLit:phi0474.phi056.perseus-lat1-text:2.7.")
            for value in values:
                found = tokens.filter(word_value=Token.get_word_value(value))
                for token in found:
                    token_lookup[token.ve_ref].append(entity)
    return token_lookup


def load_entities(input_path, version_urn):
    entities_lookup = build_entities_lookup(input_path, version_urn)
    token_lookup = build_token_lookup(entities_lookup)
    return entities_lookup, token_lookup


def add_plieades_data(plieades_pids_path, entities):
    lookup = json.load(plieades_pids_path.open())
    s = requests.Session()
    for entity, pid in lookup.items():
        try:
            entity = entities[entity]
        except KeyError:
            print(f'No entity extracted for "{entity}"')
            continue

        data = s.get(f"https://pleiades.stoa.org{pid}/json").json()
        if not data["reprPoint"]:
            continue
        time.sleep(0.25)

        # NOTE: Keep existing fields from LitViz
        entity.update(
            dict(
                # title=data["title"],
                description=data["description"],
                url=f"https://pleiades.stoa.org{pid}",
            )
        )
        # NOTE: Pleiades returns data in long, lat by default
        # lat_long = reversed(data["reprPoint"])
        # entity["data"] = dict(
        #     coordinates=", ".join([str(p) for p in lat_long])
        # )


def build_collection(entities):
    sorted_entities = sorted(entities.keys())
    idx = 0
    collection = dict(
        label="Places from Cicero's Letters",
        urn="urn:cite2:beyond-translation:named_entity_collection.atlas_v1:cicero_places",
        metadata=dict(
            attributions=[
                dict(name="Patrick Feeney", role="Annotator"),
                dict(name="Peter Nadel", role="Annotator"),
            ]
        ),
        entities=[],
    )

    urn_lookup = {}
    base_urn = "urn:cite2:beyond-translation:place.atlas_v1:cicero_places-"
    for key in sorted_entities:
        entity = entities[key]
        urn = f"{base_urn}{idx}"
        entity["urn"] = urn
        collection["entities"].append(entity)
        urn_lookup[key] = urn
        idx += 1
    return (collection, urn_lookup)


def write_collection(output_path, collection):
    with output_path.open("w") as f:
        # TODO: Sort consistently
        yaml.safe_dump(collection, f, sort_keys=False)


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
    input_path = Path("data/raw/cicero-feeney-nadel/dataframe.csv")
    version_urn = "urn:cts:latinLit:phi0474.phi056.perseus-lat1-text:"
    entities, token_lookup = load_entities(input_path, version_urn)

    # TODO: Tie to Pleiades
    plieades_pids_path = Path("data/raw/cicero-feeney-nadel/pids.json")

    add_plieades_data(plieades_pids_path, entities)

    collection, urn_lookup = build_collection(entities)

    collection_path = Path(
        "data/annotations/named-entities/processed/collections/cicero_places.yml"
    )
    write_collection(collection_path, collection)

    standoff_rows = build_standoff_annotations(version_urn, token_lookup, urn_lookup)

    standoff_path = Path(
        "data/annotations/named-entities/processed/standoff/cicero_places.csv"
    )

    write_standoff_annotations(standoff_path, standoff_rows)


if __name__ == "__main__":
    main()
