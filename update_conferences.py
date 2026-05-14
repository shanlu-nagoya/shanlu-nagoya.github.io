"""
Weekly conference tracker.
Data sources:
  1. ccf-deadlines GitHub repo  — authoritative for submission deadlines
  2. IEICE CS calendar          — IEICE international conferences
  3. IEEE ITSOC upcoming events — ISIT, ITW dates/locations
  4. IEEE VT Society            — VTC Spring/Fall dates/locations
Outputs conferences/data.json for the public website.
"""

import io
import json
import re
import sys
import time
from datetime import datetime, timezone

import requests
import yaml
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
}
IEICE_HEADERS = {**HEADERS, "Referer": "https://www.ieice.org/", "Accept-Language": "ja,en-US;q=0.9"}
OUTPUT_FILE = "conferences/data.json"

# ── ccf-deadlines sources ──────────────────────────────────────────────────────
RAW_BASE = "https://raw.githubusercontent.com/ccfddl/ccf-deadlines/main/conference"
CCF_SOURCES = [
    ("NW", "icc",      "IEEE", "Communications"),
    ("NW", "globecom", "IEEE", "Communications"),
    ("NW", "wcnc",     "IEEE", "Communications"),
    ("NW", "infocom",  "IEEE", "Communications"),
    ("CT", "isit",     "IEEE", "Information Theory"),
]

# ── Manually maintained fallback list (sites that block scrapers) ─────────────
MANUAL_CONFERENCES = [
    # VTC — vtsociety.org frequently returns 403
    {
        "name": "VTC2025-Spring",
        "full_name": "IEEE 101st Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2024-11-07", "notification": None,
        "start": "2025-06-17", "end": "2025-06-20",
        "location": "Oslo, Norway",
        "url": "https://events.vtsociety.org/vtc2025-spring/",
    },
    {
        "name": "VTC2025-Fall",
        "full_name": "IEEE 102nd Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-03-05", "notification": None,
        "start": "2025-10-19", "end": "2025-10-22",
        "location": "Chengdu, China",
        "url": "https://events.vtsociety.org/vtc2025-fall/",
    },
    {
        "name": "VTC2026-Spring",
        "full_name": "IEEE 103rd Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2026-01-04", "notification": None,
        "start": "2026-06-09", "end": "2026-06-12",
        "location": "Nice, France",
        "url": "https://events.vtsociety.org/vtc2026-spring/",
    },
    {
        "name": "VTC2026-Fall",
        "full_name": "IEEE 104th Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2026-03-21", "notification": None,
        "start": "2026-09-06", "end": "2026-09-09",
        "location": "Boston, MA, USA",
        "url": "https://events.vtsociety.org/vtc2026-fall/",
    },
    # ITW — itsoc.org frequently returns 403
    {
        "name": "ITW 2025",
        "full_name": "IEEE Information Theory Workshop",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": "2025-04-21", "notification": None,
        "start": "2025-09-29", "end": "2025-10-03",
        "location": "Sydney, Australia",
        "url": "https://www.ieee-itw2025.org/",
    },
    {
        "name": "ITW 2026",
        "full_name": "IEEE Information Theory Workshop",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": "2026-05-03", "notification": None,
        "start": "2026-11-10", "end": "2026-11-13",
        "location": "Tempe, AZ, USA",
        "url": "https://2026.ieee-itw.org/",
    },
    # ISIT 2025 — missing from CCF yml
    {
        "name": "ISIT 2025",
        "full_name": "IEEE International Symposium on Information Theory",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": "2025-01-15", "notification": None,
        "start": "2025-06-22", "end": "2025-06-27",
        "location": "Ann Arbor, MI, USA",
        "url": "https://2025.ieee-isit.org/",
    },
]

# ── Country name map for IEICE Japanese location strings ──────────────────────
IEICE_COUNTRY = {
    "日本": "Japan", "台湾": "Taiwan", "中国": "China", "アメリカ": "USA",
    "メキシコ": "Mexico", "オーストラリア": "Australia", "ドイツ": "Germany",
    "フランス": "France", "イタリア": "Italy", "カナダ": "Canada",
    "韓国": "Korea", "シンガポール": "Singapore", "インド": "India",
    "イギリス": "UK", "スペイン": "Spain", "ポルトガル": "Portugal",
    "オランダ": "Netherlands", "スウェーデン": "Sweden", "ベルギー": "Belgium",
    "スイス": "Switzerland", "ギリシャ": "Greece", "タイ": "Thailand",
    "インドネシア": "Indonesia", "マレーシア": "Malaysia", "フィリピン": "Philippines",
    "ベトナム": "Vietnam", "ブラジル": "Brazil", "アラブ首長国連邦": "UAE",
}
IEICE_CITY = {
    # Japanese cities
    "東京": "Tokyo", "大阪": "Osaka", "名古屋": "Nagoya", "福岡": "Fukuoka",
    "岡山": "Okayama", "京都": "Kyoto", "横浜": "Yokohama", "札幌": "Sapporo",
    "仙台": "Sendai", "広島": "Hiroshima", "神戸": "Kobe", "奈良": "Nara",
    "つくば": "Tsukuba", "沖縄": "Okinawa",
    # Chinese/Taiwanese cities
    "台北": "Taipei", "上海": "Shanghai", "北京": "Beijing", "成都": "Chengdu",
    "深圳": "Shenzhen", "香港": "Hong Kong", "広州": "Guangzhou",
    # Korean cities
    "釜山": "Busan", "ソウル": "Seoul",
    # Southeast Asian
    "バンコク": "Bangkok", "クアラルンプール": "Kuala Lumpur", "シンガポール": "Singapore",
    "ジャカルタ": "Jakarta",
}

# Keywords to filter IEICE conferences relevant to communications/information
IEICE_COMM_KEYWORDS = [
    "communication", "wireless", "optical", "photonic", "information",
    "network", "signal", "emerging", "intelligent", "ict",
]

# ─────────────────────────────────────────────────────────────────────────────
# Generic date helpers
# ─────────────────────────────────────────────────────────────────────────────

def iso(year: int, month: int, day: int) -> str:
    return f"{year}-{month:02d}-{day:02d}"


def parse_month_name(s: str) -> int | None:
    for fmt in ("%B", "%b"):
        try:
            return datetime.strptime(s.strip(), fmt).month
        except ValueError:
            pass
    return None


def parse_date_range_en(s: str) -> tuple[str | None, str | None]:
    """Parse English date ranges like 'June 28 - July 3, 2026' or 'Nov 10-13, 2026'."""
    s = s.strip()
    # "June 28 - July 3, 2026" or "Jun 28 - Jul 3, 2026"
    m = re.search(r"(\w+)\s+(\d+)\s*[-–]\s*(\w+)\s+(\d+),?\s*(\d{4})", s)
    if m:
        m1, d1, m2, d2, yr = m.groups()
        mo1 = parse_month_name(m1)
        mo2 = parse_month_name(m2)
        if mo1 and mo2:
            return iso(int(yr), mo1, int(d1)), iso(int(yr), mo2, int(d2))

    # "November 10-13, 2026" or "Jun 9-12, 2026"
    m = re.search(r"(\w+)\s+(\d+)[-–](\d+),?\s*(\d{4})", s)
    if m:
        mon, d1, d2, yr = m.groups()
        mo = parse_month_name(mon)
        if mo:
            return iso(int(yr), mo, int(d1)), iso(int(yr), mo, int(d2))

    # "9 Jun 2026 – 12 Jun 2026" (VTS card format)
    m = re.search(r"(\d+)\s+(\w+)\s+(\d{4})\s*[-–]\s*(\d+)\s+(\w+)\s+(\d{4})", s)
    if m:
        d1, m1, yr1, d2, m2, yr2 = m.groups()
        mo1 = parse_month_name(m1)
        mo2 = parse_month_name(m2)
        if mo1 and mo2:
            return iso(int(yr1), mo1, int(d1)), iso(int(yr2), mo2, int(d2))

    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# Source 1: ccf-deadlines
# ─────────────────────────────────────────────────────────────────────────────

def _parse_ccf_deadline(timeline: list[dict]) -> str | None:
    if not timeline:
        return None
    dl = timeline[-1].get("deadline") or timeline[-1].get("abstract_deadline")
    if not dl:
        return None
    try:
        return datetime.strptime(str(dl).strip(), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
    except ValueError:
        return str(dl)[:10]


def _parse_ccf_dates(date_str: str | None) -> tuple[str | None, str | None]:
    if not date_str:
        return None, None
    return parse_date_range_en(str(date_str))


def load_ccf_conferences() -> dict[str, dict]:
    """Returns dict keyed by conference short name (e.g. 'ISIT 2026')."""
    result: dict[str, dict] = {}
    current_year = datetime.now().year

    for category, filename, org, cat in CCF_SOURCES:
        url = f"{RAW_BASE}/{category}/{filename}.yml"
        print(f"Fetching {filename}.yml ...")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = yaml.safe_load(resp.text)
        except Exception as e:
            print(f"  Failed: {e}")
            continue

        meta = data[0]
        title = meta.get("title", filename.upper())
        description = meta.get("description", "")

        for ed in meta.get("confs", []):
            year = ed.get("year", 0)
            if year < current_year - 1:
                continue
            deadline = _parse_ccf_deadline(ed.get("timeline", []))
            start, end = _parse_ccf_dates(ed.get("date"))
            key = f"{title} {year}"
            entry = {
                "name":         key,
                "full_name":    description,
                "organizer":    org,
                "category":     cat,
                "deadline":     deadline,
                "notification": None,
                "start":        start,
                "end":          end,
                "location":     ed.get("place", "TBD"),
                "url":          ed.get("link", ""),
            }
            result[key] = entry
            print(f"  + {key} — deadline: {deadline}")

        time.sleep(0.5)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Source 2: IEICE CS calendar
# ─────────────────────────────────────────────────────────────────────────────

def _ieice_location(s: str) -> str:
    if "・" in s:
        country_ja, city_ja = s.split("・", 1)
        country_en = IEICE_COUNTRY.get(country_ja, country_ja)
        city_en = IEICE_CITY.get(city_ja, city_ja)
        return f"{city_en}, {country_en}"
    return s


def _ieice_dates(s: str) -> tuple[str | None, str | None]:
    s = s.strip()
    # "2026.11.23～11.25"
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})[～~](\d{1,2})\.(\d{1,2})", s)
    if m:
        yr, m1, d1, m2, d2 = m.groups()
        return iso(int(yr), int(m1), int(d1)), iso(int(yr), int(m2), int(d2))
    # "2026.9.6" (single day)
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", s)
    if m:
        yr, mo, da = m.groups()
        d = iso(int(yr), int(mo), int(da))
        return d, d
    return None, None


def _ieice_deadline(s: str) -> str | None:
    s = s.strip()
    if not s or s.upper() == "TBD":
        return None
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", s)
    if m:
        yr, mo, da = m.groups()
        return iso(int(yr), int(mo), int(da))
    return None


def _ieice_short_name(full_name: str) -> str:
    # Extract abbreviation like "ICETC2026" from "(ICETC2026)"
    m = re.search(r"\(([A-Z][A-Z0-9]+\d{4})\)", full_name)
    if m:
        return m.group(1)
    # Use first significant word
    words = full_name.split()
    for w in words:
        if re.match(r"^[A-Z]{2,}", w):
            return w
    return full_name[:20]


def scrape_ieice_calendar() -> list[dict]:
    url = "https://www.ieice.org/cs_r/jpn/events/conferences/calendar.html"
    print("\nScraping IEICE CS calendar...")
    try:
        r = requests.get(url, headers=IEICE_HEADERS, timeout=20)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    table = soup.find("table")
    if not table:
        return []

    results = []
    current_year = datetime.now().year

    for row in table.find_all("tr")[1:]:  # skip header
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) < 5:
            continue
        date_raw, conf_name, location_raw, deadline_raw, organizer = cells[:5]

        # Only include IEICE-CS primary-organized, communications-related conferences
        if not organizer.startswith("電子情報通信学会"):
            continue
        if not any(k in conf_name.lower() for k in IEICE_COMM_KEYWORDS):
            continue

        start, end = _ieice_dates(date_raw)
        if not start:
            continue

        # Skip past conferences
        year = int(start[:4]) if start else 0
        if year < current_year - 1:
            continue

        short = _ieice_short_name(conf_name)
        entry = {
            "name":         short,
            "full_name":    conf_name,
            "organizer":    "IEICE",
            "category":     "Communications",
            "deadline":     _ieice_deadline(deadline_raw),
            "notification": None,
            "start":        start,
            "end":          end,
            "location":     _ieice_location(location_raw),
            "url":          url,
        }
        results.append(entry)
        print(f"  + {short} — {start} — {entry['location']}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Source 3: ITSOC upcoming events (ISIT, ITW)
# ─────────────────────────────────────────────────────────────────────────────

_KNOWN_COUNTRIES = [
    "USA", "China", "Japan", "Germany", "France", "UK", "Canada",
    "Italy", "Australia", "Taiwan", "India", "Korea", "Brazil",
    "Sweden", "Netherlands", "Switzerland", "Singapore", "Greece",
    "Arizona", "California", "Texas", "Georgia",  # US states also accepted
]

def _itsoc_location(text: str) -> str | None:
    """Extract 'City[, State], Country' from event description text."""
    for country in _KNOWN_COUNTRIES:
        idx = text.find(country)
        if idx == -1:
            continue
        pre = text[max(0, idx - 50): idx]
        # Find last "City" or "City, State" before the country token
        m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)?)[\s,]*$", pre)
        if m:
            city_part = m.group(1).strip().rstrip(",")
            return f"{city_part}, {country}"
    return None


def scrape_itsoc_events() -> list[dict]:
    url = "https://www.itsoc.org/news-events/upcoming-events"
    print("\nScraping ITSOC upcoming events...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    lines = soup.get_text(separator="\n", strip=True).split("\n")
    results: list[dict] = []
    seen: set[str] = set()

    TARGETS = [
        ("ISIT", "IEEE International Symposium on Information Theory", "Information Theory"),
        ("ITW",  "IEEE Information Theory Workshop",                   "Information Theory"),
    ]

    current_year = datetime.now().year
    for abbr, full_desc, cat in TARGETS:
        for i, line in enumerate(lines):
            # Match lines like "2026 IEEE Information Theory Workshop (ITW)"
            if abbr in line and "IEEE" in line and re.search(r"20\d\d", line):
                year_m = re.search(r"(20\d\d)", line)
                if not year_m:
                    continue
                year = year_m.group(1)
                if int(year) < current_year - 1 or int(year) > current_year + 2:
                    continue
                key = f"{abbr} {year}"
                if key in seen:
                    continue

                # Gather context from nearby lines (description usually follows)
                context = " ".join(lines[i : min(len(lines), i + 4)])
                start, end = parse_date_range_en(context)
                location = _itsoc_location(context)

                seen.add(key)
                entry = {
                    "name":         key,
                    "full_name":    full_desc,
                    "organizer":    "IEEE",
                    "category":     cat,
                    "deadline":     None,
                    "notification": None,
                    "start":        start,
                    "end":          end,
                    "location":     location or "TBD",
                    "url":          url,
                }
                results.append(entry)
                print(f"  + {key} — {start} — {location}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Source 4: VT Society (VTC Spring / Fall)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_vtc_conferences() -> list[dict]:
    url = "https://vtsociety.org/conferences/about-conferences"
    print("\nScraping VT Society conference page...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    results: list[dict] = []
    current_year = datetime.now().year

    # Each VTC event is in a div.card--event
    cards = soup.find_all("div", class_=lambda c: c and "card--event" in c)
    for card in cards:
        text = card.get_text(separator="|", strip=True)
        parts = [p.strip() for p in text.split("|") if p.strip()]

        # Find acronym (VTC2026-Spring etc.)
        acronym = ""
        full_name = ""
        for j, p in enumerate(parts):
            if re.match(r"VTC\d{4}-", p):
                acronym = p
                if j + 1 < len(parts):
                    full_name = parts[j + 1]
                break

        if not acronym:
            continue

        year_m = re.search(r"(20\d\d)", acronym)
        if not year_m or int(year_m.group(1)) < current_year - 1:
            continue

        # Date: look for "9 Jun 2026" pattern
        date_str = ""
        for j, p in enumerate(parts):
            if re.match(r"\d+ \w+ 20\d\d", p) and j + 2 < len(parts):
                date_str = f"{p} – {parts[j+2]}"
                break

        start, end = parse_date_range_en(date_str) if date_str else (None, None)

        # Location: item after "Geographic Location"
        location = "TBD"
        for j, p in enumerate(parts):
            if "Geographic Location" in p and j + 1 < len(parts):
                location = parts[j + 1]
                break

        # Official site link
        link_tag = card.find("a", href=True)
        conf_url = link_tag["href"] if link_tag else url

        entry = {
            "name":         acronym,
            "full_name":    full_name,
            "organizer":    "IEEE",
            "category":     "Communications",
            "deadline":     None,
            "notification": None,
            "start":        start,
            "end":          end,
            "location":     location,
            "url":          conf_url,
        }
        results.append(entry)
        print(f"  + {acronym} — {start} — {location}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Merge logic
# ─────────────────────────────────────────────────────────────────────────────

def normalize_key(name: str) -> str:
    """Normalize conference name for deduplication matching."""
    return re.sub(r"\s+", " ", name.strip().upper())


def merge_into(base: dict[str, dict], scraped: list[dict]) -> None:
    """
    Merge scraped entries into base dict.
    - If key exists: fill in TBD fields (location, dates) but keep ccf deadline.
    - If key is new: add as new entry.
    """
    base_keys_norm = {normalize_key(k): k for k in base}

    for entry in scraped:
        nk = normalize_key(entry["name"])
        if nk in base_keys_norm:
            existing = base[base_keys_norm[nk]]
            # Only update TBD fields; never overwrite a real deadline
            if not existing.get("location") or existing["location"] == "TBD":
                existing["location"] = entry["location"]
            if not existing.get("start") and entry.get("start"):
                existing["start"] = entry["start"]
            if not existing.get("end") and entry.get("end"):
                existing["end"] = entry["end"]
            if not existing.get("url") and entry.get("url"):
                existing["url"] = entry["url"]
            # Only use scraped deadline if ccf has none
            if not existing.get("deadline") and entry.get("deadline"):
                existing["deadline"] = entry["deadline"]
        else:
            base[entry["name"]] = entry
            base_keys_norm[nk] = entry["name"]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def sort_conferences(confs: list[dict]) -> list[dict]:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tbd      = [c for c in confs if not c["deadline"]]
    upcoming = [c for c in confs if c["deadline"] and c["deadline"] >= today_str]
    past     = [c for c in confs if c["deadline"] and c["deadline"] <  today_str]
    upcoming.sort(key=lambda c: c["deadline"])
    past.sort(key=lambda c: c["deadline"], reverse=True)
    return [*tbd, *upcoming, *past]


def main() -> None:
    # 1. ccf-deadlines (authoritative deadlines)
    all_data = load_ccf_conferences()

    # 1b. manual fallback (VTC, ITW, ISIT 2025 — scrapers blocked by 403)
    merge_into(all_data, MANUAL_CONFERENCES)

    # 2. IEICE CS calendar
    merge_into(all_data, scrape_ieice_calendar())
    time.sleep(1)

    # 3. ITSOC (ISIT, ITW)
    merge_into(all_data, scrape_itsoc_events())
    time.sleep(1)

    # 4. VT Society (VTC)
    merge_into(all_data, scrape_vtc_conferences())

    conferences = sort_conferences(list(all_data.values()))

    output = {
        "updated":     datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "conferences": conferences,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(conferences)} conference editions written to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
