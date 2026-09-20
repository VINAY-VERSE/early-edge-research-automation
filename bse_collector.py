import feedparser
import requests
import json
import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from html import unescape


# ============================================================
# CONFIG
# ============================================================

BSE_RSS_URL = "https://beta.bseindia.com/data/xml/announcements.xml"

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

JSON_FILE = OUTPUT_DIR / "bse_announcements.json"
CSV_FILE = OUTPUT_DIR / "bse_announcements.csv"


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Remove HTML and normalize whitespace."""

    if not value:
        return ""

    value = unescape(str(value))

    # Remove HTML tags
    value = re.sub(r"<[^>]+>", " ", value)

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def extract_scrip_code(title):
    """
    Extract six-digit BSE scrip code from:
    Company Name (123456)
    """

    match = re.search(r"\((\d{6})\)", title)

    if match:
        return match.group(1)

    return ""


def extract_company_name(title):
    """
    Extract company name from:
    Company Name (123456)
    """

    match = re.match(r"^(.*?)\s*\(\d{6}\)", title)

    if match:
        return match.group(1).strip()

    return title.strip()


def create_unique_id(url, title, published):
    """
    Create a stable ID for an announcement.
    """

    value = f"BSE|{url}|{title}|{published}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# LOAD EXISTING DATA
# ============================================================

existing_announcements = []

if JSON_FILE.exists():

    try:

        with open(
            JSON_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            existing_announcements = json.load(f)

        if not isinstance(existing_announcements, list):
            existing_announcements = []

    except Exception as e:

        print(
            f"Warning: Could not read existing JSON: {e}"
        )

        existing_announcements = []


existing_ids = {
    item.get("unique_id")
    for item in existing_announcements
    if item.get("unique_id")
}


print(
    f"Existing announcements in database: "
    f"{len(existing_announcements)}"
)


# ============================================================
# FETCH BSE RSS
# ============================================================

print("\nFetching BSE RSS feed...")

response = requests.get(
    BSE_RSS_URL,
    timeout=30,
    headers={
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/153.0 Safari/537.36"
        )
    }
)

response.raise_for_status()

feed = feedparser.parse(response.content)


if feed.bozo:

    print(
        "Warning: RSS feed may contain malformed XML."
    )


entries = feed.entries

print(
    f"Announcements received from BSE RSS: "
    f"{len(entries)}"
)


# ============================================================
# PROCESS ANNOUNCEMENTS
# ============================================================

new_announcements = []


for entry in entries:

    # --------------------------------------------------------
    # Raw RSS fields
    # --------------------------------------------------------

    title = clean_text(
        entry.get("title", "")
    )

    url = clean_text(
        entry.get("link", "")
    )

    description = clean_text(
        entry.get("description", "")
    )

    published = clean_text(
        entry.get("published", "")
    )

    # Some feeds may use updated instead of published
    if not published:

        published = clean_text(
            entry.get("updated", "")
        )


    # --------------------------------------------------------
    # Company / Scrip
    # --------------------------------------------------------

    company = extract_company_name(title)

    scrip_code = extract_scrip_code(title)


    # --------------------------------------------------------
    # Unique ID
    # --------------------------------------------------------

    unique_id = create_unique_id(
        url,
        title,
        published
    )


    # --------------------------------------------------------
    # Capture ALL RSS fields
    # --------------------------------------------------------

    raw_fields = {}

    for key, value in entry.items():

        if isinstance(value, (str, int, float)):

            raw_fields[key] = clean_text(value)

        else:

            raw_fields[key] = str(value)


    # --------------------------------------------------------
    # Announcement record
    # --------------------------------------------------------

    item = {

        "unique_id": unique_id,

        "source": "BSE",

        "company": company,

        "scrip_code": scrip_code,

        "headline": title,

        "published_date": published,

        "url": url,

        "raw_text": description,

        "collected_at":
            datetime.now(timezone.utc).isoformat(),

        "rss_fields": raw_fields
    }


    # --------------------------------------------------------
    # Add only if new
    # --------------------------------------------------------

    if unique_id not in existing_ids:

        new_announcements.append(item)

        existing_ids.add(unique_id)


# ============================================================
# COMBINE OLD + NEW
# ============================================================

all_announcements = (
    existing_announcements +
    new_announcements
)


# ============================================================
# SORT BY DATE
# ============================================================

def sort_key(item):

    return item.get(
        "published_date",
        ""
    )


all_announcements.sort(
    key=sort_key,
    reverse=True
)


# ============================================================
# SAVE JSON
# ============================================================

with open(
    JSON_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_announcements,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# SAVE CSV
# ============================================================

fieldnames = [

    "unique_id",

    "source",

    "company",

    "scrip_code",

    "headline",

    "published_date",

    "url",

    "raw_text",

    "collected_at"
]


with open(
    CSV_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for item in all_announcements:

        writer.writerow({

            field: item.get(
                field,
                ""
            )

            for field in fieldnames

        })


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")

print("BSE COLLECTION COMPLETE")

print("========================================")

print(
    f"Existing records: "
    f"{len(existing_announcements)}"
)

print(
    f"New records: "
    f"{len(new_announcements)}"
)

print(
    f"Total records: "
    f"{len(all_announcements)}"
)

print(
    f"\nSaved JSON: "
    f"{JSON_FILE}"
)

print(
    f"Saved CSV: "
    f"{CSV_FILE}"
)


# ============================================================
# SAMPLE
# ============================================================

print("\nSample announcements:")


for item in all_announcements[:5]:

    print("--------------------------------")

    print(
        "Company:",
        item["company"]
    )

    print(
        "Scrip:",
        item["scrip_code"]
    )

    print(
        "Headline:",
        item["headline"]
    )

    print(
        "Date:",
        item["published_date"]
    )

    print(
        "URL:",
        item["url"]
    )

    print(
        "Raw text:",
        item["raw_text"][:300]
    )
