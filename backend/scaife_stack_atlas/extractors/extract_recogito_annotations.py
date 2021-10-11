import csv
import os
import time
from collections import defaultdict
from pathlib import Path

import django

import logfmt
import requests
from lxml import etree


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
django.setup()

RECOGITO_PATH = Path("data/raw/homer-kemp/recogito_docs")
GEO_KIMA_API_BASE_URL = f"https://geo-kima.org/api/Places/Place/"
WIKIPEDIA_PAGE_BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
GEONAMES_JSON_API_URL = "http://api.geonames.org/getJSON"

FULL_NAMES_PATH = Path("data/raw/homer-kemp/FullNames.txt")
RECOVERING_PARSER = etree.XMLParser(recover=True)

ns = {"TEI": "http://www.tei-c.org/ns/1.0"}
SUBTYPE = "book"


def make_offset(part, whole):
    parts = part.split(" ")

    exact = False
    try:
        assert whole.count(parts[0]) == 1
        start = whole.index(parts[0])
        exact = True
    except AssertionError:
        start = None
        for a_pos, a in enumerate(parts):
            for b_pos, b in enumerate(whole):
                if b.startswith(a):
                    start = b_pos
                    exact = False
                    break
        if start is None:
            assert False

    parts_len = len(parts)
    end = start + parts_len
    if whole[start:end] == parts or not exact:
        return [start + 1, end + 1]
    else:
        import pdb

        pdb.set_trace()
        assert False


def extract_lookups(base_urn, parsed):
    tokens_lookup = {}
    annotation_lookup = defaultdict(dict)
    for book in parsed.xpath(f"//TEI:div[@subtype='{SUBTYPE}']", namespaces=ns):
        book_num = book.attrib["n"]
        for line in book.xpath(".//TEI:l", namespaces=ns):
            line_num = line.attrib["n"]
            line_urn = f"{base_urn}{book_num}.{line_num}"
            tokens = tokens_lookup.setdefault(
                line_urn,
                list(
                    Token.objects.filter(text_part__urn=line_urn).values_list(
                        "word_value", flat=True
                    )
                ),
            )
            # text = re.sub(r"\s+", " ", line.xpath("string()").strip())
            for pers in line.xpath(".//TEI:persName", namespaces=ns):
                pers_text = pers.xpath("string()").strip()
                if not pers_text:
                    continue

                start, end = make_offset(pers_text, tokens)
                ve_refs = []
                if end - start == 1:
                    ve_refs = [f"{line_urn}.t{start}"]
                else:
                    for idx in range(start, end):
                        ve_refs.append(f"{line_urn}.t{idx}")
                # print(tokens[start -1: end-1])
                people = annotation_lookup[line_urn].setdefault("people", [])
                people.append(
                    {
                        "kind": "person",
                        "value": pers.attrib["ana"][1:],
                        "tokens": ve_refs,
                    }
                )
                if len(pers_text.split(" ")) > 1:
                    # print(f"{line_num} {pers_text}")
                    print(ve_refs)
            for place in line.xpath(".//TEI:placeName", namespaces=ns):
                place_text = place.xpath("string()").strip()
                make_offset(place_text, tokens)
                start, end = make_offset(place_text, tokens)
                ve_refs = []
                if end - start == 1:
                    ve_refs = [f"{line_urn}.t{start}"]
                else:
                    for idx in range(start, end):
                        ve_refs.append(f"{line_urn}.t{idx}")
                ref = place.attrib.get("ref")
                if not ref:
                    continue
                # print(tokens[start -1: end-1])
                places = annotation_lookup[line_urn].setdefault("places", [])
                places.append(
                    {"kind": "place", "value": place.attrib["ref"], "tokens": ve_refs,}
                )
    return annotation_lookup


def extract_people_records(annotation_lookup):
    # first, get unique values
    unique_people_by_value = {}
    for urn, values in annotation_lookup.items():
        for person in values.get("people", []):
            key = person["value"]
            tokens = person["tokens"]
            unique_people_by_value.setdefault(key, []).extend(tokens)
            # person_urn = value_to_urn.get(key)
            # if not person_urn:
            #     person_urn = base_person_urn.format(idx=idx)
            #     idx += 1

    people = {}
    idx = 0
    base_person_urn = "urn:cite2:beyond-translation.scaife-viewer.org:pers.v1:{idx}"
    for person in sorted(unique_people_by_value.keys()):
        data = unique_people_by_value[person]
        person_urn = base_person_urn.format(idx=idx)
        idx += 1
        people[person_urn] = {"value": person, "references": data}
    return people


def get_wikipedia_url_lookup():
    wikipedia_lu_csv = csv.reader(FULL_NAMES_PATH.open())
    rows = [r for r in wikipedia_lu_csv]
    wikipedia_lu = {}
    for (value, url) in rows:
        wikipedia_lu[value] = url.strip()
    return wikipedia_lu


def get_wikipedia_data(link, sleep_duration=0.3):
    page_title = link.rsplit("/", maxsplit=1)[1]
    print(page_title)
    wd = requests.get(f"{WIKIPEDIA_PAGE_BASE_URL}{page_title}").json()
    time.sleep(sleep_duration)
    return wd


def get_preferred_title(value, wd):
    if value != wd["title"]:
        print(f'Wikpedia title "{wd["title"]}" differs from {value}')
    return value


def prepare_person_data(wikipedia_lu, person):
    link = wikipedia_lu[person["value"]]
    wd = get_wikipedia_data(link)
    title = get_preferred_title(person["value"], wd)
    return {
        "label": title,
        "description": wd.get("description", ""),
        "link": link,
    }


def get_people_rows(people_records):
    # TODO: Handle things like 'the Greek god of the cold north wind and the bringer of winter.'
    # and also ana="#Eumaeus #Melanthius"
    # Wikpedia title "Not found." differs from Jocasta
    # ana="#athena #Athena"
    rows = []
    wikipedia_lu = get_wikipedia_url_lookup()
    for urn, data in people_records.items():
        try:
            rows.append({"urn": urn, **prepare_person_data(wikipedia_lu, data)})
        except:
            print(f"problem with {urn}")
    return rows


def write_people_rows(people_rows):
    path = Path("data/annotations/named-entities/processed/entities/od_people.csv")
    # Make sure that parent dir exists
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["urn", "label", "description", "link"]
    with open(path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in people_rows:
            writer.writerow(row)


def write_standoff_data(records, kind):
    # TODO: only export records if we have valid entities
    path = Path(
        f"data/annotations/named-entities/processed/standoff/od_{kind}_references.csv"
    )
    # Make sure that parent dir exists
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["named_entity_urn", "ref", "token_position"]
    with open(path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for urn, data in records.items():
            for reference in data["references"]:
                # TODO: Prefer ve_refs next time
                ref, token_position = reference.rsplit(".t", maxsplit=1)
                writer.writerow(
                    {
                        "named_entity_urn": urn,
                        "ref": ref,
                        "token_position": token_position,
                    }
                )


def create_people_annotations(annotations_lookup):
    people_records = extract_people_records(annotations_lookup)
    people_rows = get_people_rows(people_records)
    write_people_rows(people_rows)
    write_standoff_data(people_records, "people")


def extract_place_records(annotation_lookup):
    # first, get unique values
    unique_places_by_value = {}
    for urn, values in annotation_lookup.items():
        for place in values.get("places", []):
            key = place["value"]
            tokens = place["tokens"]
            unique_places_by_value.setdefault(key, []).extend(tokens)

    places = {}
    idx = 0
    base_place_urn = "urn:cite2:beyond-translation.scaife-viewer.org:place.v1:{idx}"
    for place in sorted(unique_places_by_value.keys()):
        data = unique_places_by_value[place]
        place_urn = base_place_urn.format(idx=idx)
        idx += 1
        places[place_urn] = {"value": place, "references": data}
    return places


def get_geo_kima_data(link, sleep_duration=0.3):
    data = {}
    place_id = link.rsplit("/", maxsplit=1)[1]
    geo_kima_data = requests.get(f"{GEO_KIMA_API_BASE_URL}{place_id}").json()
    time.sleep(sleep_duration)
    try:
        coordinates = geo_kima_data["coor"].split("(")[1].split(")")[0].split()
        long_, lat_ = coordinates
        data["coordinates"] = [lat_, long_]
    except:
        pass
    data["title"] = geo_kima_data["primary_rom_full"].strip()
    try:
        wikidata_entity_url = f'https://www.wikidata.org/wiki/Special:EntityData/{geo_kima_data["wd"]}.json'
        wikidata_data = requests.get(wikidata_entity_url).json()
        time.sleep(sleep_duration)
        data["description"] = wikidata_data["entities"][geo_kima_data["wd"]][
            "descriptions"
        ]["en"]["value"].strip()
    except:
        pass
    return data


def get_pleiades_data(url, sleep_duration=0.3):
    pleiades_data = requests.get(f"{url}/json").json()
    # NOTE: Pleiades returns data in long, lat by default
    point = reversed(pleiades_data["reprPoint"]) or []
    time.sleep(sleep_duration)
    return {
        "title": pleiades_data["title"].strip(),
        "description": pleiades_data["description"].strip(),
        "coordinates": [str(p) for p in point],
    }


def get_geonames_data(url, sleep_duration=0.3):
    geonames_id = url.rsplit("/")[-1]
    geonames_data = requests.get(
        GEONAMES_JSON_API_URL,
        params={"geonameId": geonames_id, "username": "music_research"},
    ).json()
    # point = pleiades_data["reprPoint"] or []
    time.sleep(sleep_duration)
    wd = get_wikipedia_data(geonames_data["wikipediaURL"])
    point = [geonames_data["lat"], geonames_data["lng"]]
    return {
        "title": geonames_data["name"].strip(),
        "description": wd.get("description", ""),
        "coordinates": [str(p) for p in point],
    }


# 4:54 PM stopped


def prepare_place_data(place):
    value = place["value"]
    print(f'Fetching data for "{value}"...')
    if value.count("geo-kima"):
        gkd = get_geo_kima_data(value)
        data = {
            "label": gkd["title"],
            "description": gkd.get("description", ""),
            "data": {},
            "link": value,
        }
        coordinates = gkd.get("coordinates")
        if coordinates:
            data.setdefault("data", {})["coordinates"] = ", ".join(coordinates)
        return data
    elif value.count("pleiades"):
        pd = get_pleiades_data(value)
        return {
            "label": pd["title"],
            "description": pd["description"],
            "data": {"coordinates": ", ".join(pd["coordinates"])},
            "link": value,
        }
    elif value.count("geonames"):
        gd = get_geonames_data(value)
        return {
            "label": gd["title"],
            "description": gd["description"],
            "data": {"coordinates": ", ".join(gd["coordinates"])},
            "link": value,
        }
    else:
        return {
            "label": f"{value}",
            "description": "",
            "data": {},
            "link": value,
        }


def get_place_rows(place_records):
    rows = []
    for urn, data in place_records.items():
        try:
            rows.append({"urn": urn, **prepare_place_data(data)})
        except:
            print(f"problem with {urn}")

    return rows


def logfmt_wrapped_row(row):
    wr = {}
    wr.update(**row)
    data = wr.pop("data", None)
    if data:
        wr["data"] = next(logfmt.format(data))
    return wr


def write_place_rows(place_rows):
    path = Path("data/annotations/named-entities/processed/entities/od_places.csv")
    # Make sure that parent dir exists
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["urn", "label", "description", "data", "link"]
    with open(path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in place_rows:
            prepared_row = logfmt_wrapped_row(row)
            writer.writerow(prepared_row)


def create_place_annotations(annotations_lookup):
    place_records = extract_place_records(annotations_lookup)
    place_rows = get_place_rows(place_records)
    write_place_rows(place_rows)
    write_standoff_data(place_records, "places")


def main():
    base_urn = "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:"
    all_annotations = dict()
    for path in RECOGITO_PATH.glob("*.xml"):
        parsed = etree.fromstring(path.read_bytes(), parser=RECOVERING_PARSER)
        all_annotations.update(extract_lookups(base_urn, parsed))

    create_people_annotations(all_annotations)
    create_place_annotations(all_annotations)


if __name__ == "__main__":
    main()
