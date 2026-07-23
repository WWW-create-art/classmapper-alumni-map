from __future__ import annotations

import csv
import os
import sys
from collections import OrderedDict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from geolocation import KNOWN_LOCATIONS, get_school_location, load_cache, save_cache  # noqa: E402
from html_generator import SCHOOL_ALIASES, generate_html_template  # noqa: E402


def main(argv=None):
    argv = argv or sys.argv[1:]
    input_path = argv[0] if argv else os.path.join(ROOT, "data", "jielong.csv")
    output_dir = argv[1] if len(argv) > 1 else os.path.join(ROOT, "蹭饭地图结果")

    os.makedirs(output_dir, exist_ok=True)
    records = read_csv_roster(input_path)
    print(f"✅ 成功读取名单数据，共 {len(records)} 条记录")

    cache_path = os.path.join(output_dir, "location_cache.json")
    cache = load_cache(cache_path)
    schools = unique_schools(records)
    locations = OrderedDict()
    for school in schools:
        locations[school] = get_school_location(school, cache)
    save_cache(cache, cache_path)

    markers = prepare_markers(records, locations)
    roster = prepare_roster(records, locations)
    center = calculate_center(locations)
    location_lookup = {**KNOWN_LOCATIONS, **locations}
    output_path = os.path.join(output_dir, "蹭饭地图.html")
    generate_html_template(center, markers, output_path, roster, location_lookup)


def read_csv_roster(input_path):
    records = []
    with open(input_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "姓名" not in reader.fieldnames or "学校" not in reader.fieldnames:
            raise ValueError("名单文件中必须包含'姓名'和'学校'两列")

        for index, row in enumerate(reader, start=1):
            name = str(row.get("姓名") or "").strip()
            school = normalize_school_name(row.get("学校") or "")
            if not name or not school:
                continue
            records.append({
                "order": parse_order(row.get("序号"), len(records) + 1),
                "name": name,
                "school": school,
            })
    return records


def normalize_school_name(value):
    school = str(value or "").strip()
    return SCHOOL_ALIASES.get(school, school)


def parse_order(value, fallback):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return fallback


def unique_schools(records):
    schools = OrderedDict()
    for record in records:
        schools.setdefault(record["school"], None)
    return list(schools.keys())


def prepare_markers(records, locations):
    grouped = OrderedDict()
    for record in records:
        grouped.setdefault(record["school"], []).append(record)

    markers = []
    for school, group in grouped.items():
        loc = locations[school]
        lat, lng = loc["coords"]
        markers.append({
            "lat": lat,
            "lng": lng,
            "title": school,
            "students": [record["name"] for record in group],
            "address": loc["address"],
            "count": len(group),
            "firstOrder": group[0]["order"],
        })
    return markers


def prepare_roster(records, locations):
    roster = []
    for record in records:
        loc = locations[record["school"]]
        lat, lng = loc["coords"]
        roster.append({
            "order": record["order"],
            "name": record["name"],
            "school": record["school"],
            "city": loc["city"],
            "address": loc["address"],
            "lat": lat,
            "lng": lng,
        })
    return roster


def calculate_center(locations):
    coords = [loc["coords"] for loc in locations.values() if tuple(loc["coords"]) != (0, 0)]
    if not coords:
        return [35.8617, 104.1954]
    return [
        sum(coord[0] for coord in coords) / len(coords),
        sum(coord[1] for coord in coords) / len(coords),
    ]


if __name__ == "__main__":
    main()
