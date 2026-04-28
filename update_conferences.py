"""
Weekly conference tracker.
Fetches IEEE/IEICE conference deadlines from the ccf-deadlines open dataset
(https://github.com/ccfddl/ccf-deadlines) and supplements with IEICE/other
conferences maintained in EXTRA_CONFERENCES below.
Outputs conferences/data.json for the website.
"""

import io
import json
import sys
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import yaml  # PyYAML

RAW_BASE = "https://raw.githubusercontent.com/ccfddl/ccf-deadlines/main/conference"
OUTPUT_FILE = "conferences/data.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (conference-tracker-bot/1.0)"}

# ccf-deadlines YAML files to fetch: (category, filename, organizer, display_category)
CCF_SOURCES = [
    ("NW",  "icc",      "IEEE",  "Communications"),
    ("NW",  "globecom", "IEEE",  "Communications"),
    ("NW",  "wcnc",     "IEEE",  "Communications"),
    ("NW",  "infocom",  "IEEE",  "Communications"),
    ("CT",  "isit",     "IEEE",  "Information Theory"),
]

# Conferences not in ccf-deadlines — update annually
EXTRA_CONFERENCES = [
    {
        "name": "VTC2025-Spring",
        "full_name": "IEEE 101st Vehicular Technology Conference",
        "organizer": "IEEE",
        "category": "Communications",
        "deadline": "2024-11-10",
        "notification": None,
        "start": "2025-06-22",
        "end": "2025-06-25",
        "location": "Oslo, Norway",
        "url": "https://events.vtsociety.org/vtc2025-spring/",
    },
    {
        "name": "VTC2025-Fall",
        "full_name": "IEEE 102nd Vehicular Technology Conference",
        "organizer": "IEEE",
        "category": "Communications",
        "deadline": "2025-06-01",
        "notification": None,
        "start": "2025-10-05",
        "end": "2025-10-08",
        "location": "Washington DC, USA",
        "url": "https://events.vtsociety.org/vtc2025-fall/",
    },
    {
        "name": "PIMRC 2025",
        "full_name": "IEEE 36th Annual International Symposium on Personal, Indoor and Mobile Radio Communications",
        "organizer": "IEEE",
        "category": "Communications",
        "deadline": "2025-04-15",
        "notification": None,
        "start": "2025-09-01",
        "end": "2025-09-04",
        "location": "Istanbul, Turkey",
        "url": "https://pimrc2025.ieee-pimrc.org/",
    },
    {
        "name": "ITW 2025",
        "full_name": "IEEE Information Theory Workshop",
        "organizer": "IEEE",
        "category": "Information Theory",
        "deadline": "2025-05-01",
        "notification": None,
        "start": "2025-10-12",
        "end": "2025-10-16",
        "location": "TBD",
        "url": "https://www.itsoc.org/conferences",
    },
    {
        "name": "ISITA 2026",
        "full_name": "International Symposium on Information Theory and Its Applications",
        "organizer": "IEICE",
        "category": "Information Theory",
        "deadline": None,
        "notification": None,
        "start": None,
        "end": None,
        "location": "TBD",
        "url": "https://www.isita.ieice.org/",
    },
    {
        "name": "APCC 2025",
        "full_name": "Asia-Pacific Conference on Communications",
        "organizer": "IEICE",
        "category": "Communications",
        "deadline": "2025-05-15",
        "notification": None,
        "start": "2025-11-10",
        "end": "2025-11-12",
        "location": "TBD",
        "url": "https://www.apcc.net/",
    },
    {
        "name": "SPAWC 2025",
        "full_name": "IEEE Signal Processing Advances in Wireless Communications",
        "organizer": "IEEE",
        "category": "Communications",
        "deadline": "2025-02-15",
        "notification": None,
        "start": "2025-09-01",
        "end": "2025-09-04",
        "location": "TBD",
        "url": "https://2025.ieeespawc.org/",
    },
]


def fetch_yaml(category: str, filename: str) -> list[dict] | None:
    url = f"{RAW_BASE}/{category}/{filename}.yml"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return yaml.safe_load(resp.text)
    except Exception as e:
        print(f"  Failed to fetch {filename}.yml: {e}")
        return None


def parse_deadline(timeline: list[dict], timezone_str: str) -> str | None:
    if not timeline:
        return None
    entry = timeline[-1]  # take the last deadline (e.g., extended)
    dl = entry.get("deadline") or entry.get("abstract_deadline")
    if not dl:
        return None
    try:
        dt = datetime.strptime(str(dl).strip(), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return str(dl)[:10]


def parse_date_range(date_str: str | None) -> tuple[str | None, str | None]:
    if not date_str:
        return None, None
    s = str(date_str).strip()
    import re
    # "June 8-12, 2025"
    m = re.match(r"(\w+)\s+(\d+)-(\d+),?\s*(\d{4})", s)
    if m:
        mon, d1, d2, yr = m.groups()
        try:
            start = datetime.strptime(f"{mon} {d1} {yr}", "%B %d %Y").strftime("%Y-%m-%d")
            end   = datetime.strptime(f"{mon} {d2} {yr}", "%B %d %Y").strftime("%Y-%m-%d")
            return start, end
        except ValueError:
            pass
    # "June 28 - July 3, 2026"
    m = re.match(r"(\w+)\s+(\d+)\s*[-–]\s*(\w+)\s+(\d+),?\s*(\d{4})", s)
    if m:
        m1, d1, m2, d2, yr = m.groups()
        try:
            start = datetime.strptime(f"{m1} {d1} {yr}", "%B %d %Y").strftime("%Y-%m-%d")
            end   = datetime.strptime(f"{m2} {d2} {yr}", "%B %d %Y").strftime("%Y-%m-%d")
            return start, end
        except ValueError:
            pass
    # "March 24-27, 2025" (abbreviated month)
    m = re.match(r"(\w{3,})\s+(\d+)-(\d+),?\s*(\d{4})", s)
    if m:
        mon, d1, d2, yr = m.groups()
        for fmt in ("%b %d %Y", "%B %d %Y"):
            try:
                start = datetime.strptime(f"{mon} {d1} {yr}", fmt).strftime("%Y-%m-%d")
                end   = datetime.strptime(f"{mon} {d2} {yr}", fmt).strftime("%Y-%m-%d")
                return start, end
            except ValueError:
                continue
    return None, None


def load_ccf_conferences() -> list[dict]:
    results = []
    for category, filename, org, cat in CCF_SOURCES:
        print(f"Fetching {filename}.yml ({category})...")
        data = fetch_yaml(category, filename)
        if not data:
            continue

        conf_meta = data[0]
        title = conf_meta.get("title", filename.upper())
        description = conf_meta.get("description", "")
        editions = conf_meta.get("confs", [])

        # Keep upcoming editions (most recent 2 years)
        current_year = datetime.now().year
        for ed in editions:
            year = ed.get("year", 0)
            if year < current_year - 1:
                continue
            deadline = parse_deadline(ed.get("timeline", []), ed.get("timezone", "UTC"))
            start, end = parse_date_range(ed.get("date"))
            entry = {
                "name": f"{title} {year}",
                "full_name": description,
                "organizer": org,
                "category": cat,
                "deadline": deadline,
                "notification": None,
                "start": start,
                "end": end,
                "location": ed.get("place", "TBD"),
                "url": ed.get("link", ""),
            }
            results.append(entry)
            print(f"  + {entry['name']} — deadline: {deadline} — {entry['location']}")

    return results


def main() -> None:
    all_conferences: list[dict] = []

    # 1. Fetch from ccf-deadlines
    ccf_entries = load_ccf_conferences()
    all_conferences.extend(ccf_entries)

    # 2. Add supplemental entries
    print("\nAdding supplemental conferences...")
    for entry in EXTRA_CONFERENCES:
        all_conferences.append(entry)
        print(f"  + {entry['name']} — deadline: {entry['deadline']}")

    # Sort by deadline (None goes to the end)
    all_conferences.sort(key=lambda c: c["deadline"] or "9999-99-99")

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "conferences": all_conferences,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(all_conferences)} conference editions written to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
