"""
Conference tracker — manually maintained, no web scraping.
To add or update a conference: edit CONFERENCES below, then run:
    python update_conferences.py
Outputs conferences/data.json for the public website.
"""

import io
import json
import sys
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUTPUT_FILE = "conferences/data.json"

# Fields: name, full_name, organizer, category,
#         deadline (YYYY-MM-DD or null), notification (or null),
#         start (YYYY-MM-DD or null), end (YYYY-MM-DD or null),
#         location, url
CONFERENCES = [
    # ── 2025 ─────────────────────────────────────────────────────────────────
    {
        "name": "WCNC 2025",
        "full_name": "IEEE Wireless Communications and Networking Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2024-09-02", "notification": None,
        "start": "2025-03-24", "end": "2025-03-27",
        "location": "Milan, Italy",
        "url": "https://wcnc2025.ieee-wcnc.org/",
    },
    {
        "name": "INFOCOM 2025",
        "full_name": "IEEE International Conference on Computer Communications",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2024-07-31", "notification": None,
        "start": "2025-05-19", "end": "2025-05-22",
        "location": "London, UK",
        "url": "https://infocom2025.ieee-infocom.org/",
    },
    {
        "name": "ICC 2025",
        "full_name": "IEEE International Conference on Communications",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2024-10-11", "notification": None,
        "start": "2025-06-08", "end": "2025-06-12",
        "location": "Montreal, Canada",
        "url": "https://icc2025.ieee-icc.org/",
    },
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
        "name": "ISIT 2025",
        "full_name": "IEEE International Symposium on Information Theory",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": "2025-01-15", "notification": None,
        "start": "2025-06-22", "end": "2025-06-27",
        "location": "Ann Arbor, MI, USA",
        "url": "https://2025.ieee-isit.org/",
    },
    {
        "name": "ICCC 2025",
        "full_name": "IEEE/CIC International Conference on Communications in China",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-04-01", "notification": None,
        "start": "2025-08-10", "end": "2025-08-13",
        "location": "Shanghai, China",
        "url": "https://iccc2025.ieee-iccc.org/",
    },
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
        "name": "VTC2025-Fall",
        "full_name": "IEEE 102nd Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-03-05", "notification": None,
        "start": "2025-10-19", "end": "2025-10-22",
        "location": "Chengdu, China",
        "url": "https://events.vtsociety.org/vtc2025-fall/",
    },
    {
        "name": "GLOBECOM 2025",
        "full_name": "IEEE Global Communications Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-04-15", "notification": None,
        "start": "2025-12-08", "end": "2025-12-12",
        "location": "Taipei, Taiwan",
        "url": "https://globecom2025.ieee-globecom.org/",
    },
    # ── 2026 ─────────────────────────────────────────────────────────────────
    {
        "name": "WCNC 2026",
        "full_name": "IEEE Wireless Communications and Networking Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-09-14", "notification": None,
        "start": "2026-04-13", "end": "2026-04-16",
        "location": "Kuala Lumpur, Malaysia",
        "url": "https://wcnc2026.ieee-wcnc.org/",
    },
    {
        "name": "ICC 2026",
        "full_name": "IEEE International Conference on Communications",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-10-31", "notification": None,
        "start": "2026-05-24", "end": "2026-05-28",
        "location": "Glasgow, Scotland, UK",
        "url": "https://icc2026.ieee-icc.org/",
    },
    {
        "name": "ISIT 2026",
        "full_name": "IEEE International Symposium on Information Theory",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": "2026-01-16", "notification": None,
        "start": "2026-06-28", "end": "2026-07-03",
        "location": "Guangzhou, China",
        "url": "https://2026.ieee-isit.org/",
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
        "name": "INFOCOM 2026",
        "full_name": "IEEE International Conference on Computer Communications",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2025-07-31", "notification": None,
        "start": None, "end": None,
        "location": "TBD",
        "url": "https://infocom2026.ieee-infocom.org/",
    },
    {
        "name": "ICCC 2026",
        "full_name": "IEEE/CIC International Conference on Communications in China",
        "organizer": "IEEE", "category": "Communications",
        "deadline": None, "notification": None,
        "start": "2026-08-07", "end": "2026-08-10",
        "location": "Wuhan, China",
        "url": "https://iccc2026.ieee-iccc.org/",
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
    {
        "name": "ITW 2026",
        "full_name": "IEEE Information Theory Workshop",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": "2026-05-03", "notification": None,
        "start": "2026-11-10", "end": "2026-11-13",
        "location": "Tempe, AZ, USA",
        "url": "https://2026.ieee-itw.org/",
    },
    {
        "name": "APCC 2026",
        "full_name": "Asia-Pacific Conference on Communications",
        "organizer": "IEICE/IEEE", "category": "Communications",
        "deadline": None, "notification": None,
        "start": "2026-11-10", "end": "2026-11-12",
        "location": "Xi'an, China",
        "url": "https://apcc2026.org/",
    },
    {
        "name": "GLOBECOM 2026",
        "full_name": "IEEE Global Communications Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": "2026-05-03", "notification": None,
        "start": "2026-12-07", "end": "2026-12-11",
        "location": "Macau, China",
        "url": "https://globecom2026.ieee-globecom.org/",
    },
    # ── 2027 ─────────────────────────────────────────────────────────────────
    {
        "name": "ICC 2027",
        "full_name": "IEEE International Conference on Communications",
        "organizer": "IEEE", "category": "Communications",
        "deadline": None, "notification": None,
        "start": "2027-05-30", "end": "2027-06-03",
        "location": "Washington, DC, USA",
        "url": "https://icc2027.ieee-icc.org/",
    },
    {
        "name": "VTC2027-Spring",
        "full_name": "IEEE 105th Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": None, "notification": None,
        "start": "2027-06-20", "end": "2027-06-23",
        "location": "Hamburg, Germany",
        "url": "https://events.vtsociety.org/vtc2027-spring/",
    },
    {
        "name": "ISIT 2027",
        "full_name": "IEEE International Symposium on Information Theory",
        "organizer": "IEEE", "category": "Information Theory",
        "deadline": None, "notification": None,
        "start": "2027-06-27", "end": "2027-07-02",
        "location": "Sorrento, Italy",
        "url": "https://2027.ieee-isit.org/",
    },
    {
        "name": "VTC2027-Fall",
        "full_name": "IEEE 106th Vehicular Technology Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": None, "notification": None,
        "start": None, "end": None,
        "location": "Osaka, Japan",
        "url": "https://events.vtsociety.org/vtc2027-fall/",
    },
    {
        "name": "GLOBECOM 2027",
        "full_name": "IEEE Global Communications Conference",
        "organizer": "IEEE", "category": "Communications",
        "deadline": None, "notification": None,
        "start": "2027-12-06", "end": "2027-12-10",
        "location": "Abu Dhabi, UAE",
        "url": "https://globecom2027.ieee-globecom.org/",
    },
]


def sort_conferences(confs: list[dict]) -> list[dict]:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tbd      = [c for c in confs if not c["deadline"]]
    upcoming = [c for c in confs if c["deadline"] and c["deadline"] >= today_str]
    past     = [c for c in confs if c["deadline"] and c["deadline"] <  today_str]
    upcoming.sort(key=lambda c: c["deadline"])
    past.sort(key=lambda c: c["deadline"], reverse=True)
    return [*tbd, *upcoming, *past]


def main() -> None:
    conferences = sort_conferences(CONFERENCES)
    output = {
        "updated":     datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "conferences": conferences,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Done. {len(conferences)} conferences written to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
