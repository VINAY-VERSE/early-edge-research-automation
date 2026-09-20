import feedparser
import requests
import json
import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from html import unescape

BSE_RSS_URL = "https://beta.bseindia.com/data/xml/announcements.xml"

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

JSON_FILE = OUTPUT_DIR / "bse_announcements.json"
CSV_FILE = OUTPUT_DIR / "bse_announcements.csv"


def clean_html(text):
    """
    Remove HTML tags and clean whitespace.
    """
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_scrip_code(title):
    """
    Extract 6-digit BSE scrip code from:
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


def extract_headline(title, description):
    """
    Remove company name and scrip code from the beginning
    of the BSE title.

    Example:

    Input:
        Netweb Technologies India Ltd (543945) - Board Meeting

    Output:
        Board Meeting

    If the title contains only:
        Netweb Technologies India Ltd (543945)

    then use the description as fallback.
    """

    title = clean_html(title)
    description = clean_html(description)

    # Remove company name + scrip code from beginning
    headline = re.sub(
        r"^.*?\s*\(\d{6}\)\s*[-–—:]?\s*",
        "",
        title,
        count=1
    ).strip()

    # Remove common separators left at beginning
    headline = re.sub(
        r"^[\s\-–—:|]+",
        "",
        headline
    ).strip()

    # If nothing meaningful remains, use description
    if not headline:

        if description:

            # Try to use the first sentence/line
            fallback = re.split(
                r"(?<=[.!?])\s+|\n+",
                description
            )[0].strip()

            headline = fallback[:500]

    return headline


def create_unique_id(url, title):
    """
    Create a stable unique ID for each announcement.
    """

    value = f"BSE|{url}|{title}"

    return hashlib.sha256(
        value.encode()
    ).hexdigest()[:16]


print("Fetching BSE RSS feed...")

response = requests.get(
    BSE_RSS_URL,
    timeout=30,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

response.raise_for_status()

feed = feedparser.parse(response.content)

if feed.bozo:
    print("Warning: RSS feed may contain malformed XML.")

entries = feed.entries

print(f"Total announcements found: {len(entries)}")

announcements = []


for entry in entries:

    title = entry.get("title", "").strip()

    url = entry.get("link", "").strip()

    description = entry.get(
        "description",
        ""
    ).strip()

    published = entry.get(
        "published",
        ""
    ).strip()

    # -----------------------------------------
    # COMPANY
    # -----------------------------------------

    company = extract_company_name(title)

    # -----------------------------------------
    # SCRIP CODE
    # -----------------------------------------

    scrip_code = extract_scrip_code(title)

    # -----------------------------------------
    # CLEAN HEADLINE
    # -----------------------------------------

    headline = extract_headline(
        title,
        description
    )

    # -----------------------------------------
    # UNIQUE ID
    # -----------------------------------------

    unique_id = create_unique_id(
        url,
        title
    )

    # -----------------------------------------
    # COLLECTION TIME
    # -----------------------------------------

    collected_at = datetime.now(
        timezone.utc
    ).isoformat()

    # -----------------------------------------
    # FINAL RECORD
    # -----------------------------------------

    item = {

        "unique_id": unique_id,

        "source": "BSE",

        "company": company,

        "scrip_code": scrip_code,

        "headline": headline,

        "published_date": published,

        "url": url,

        "raw_text": description,

        "collected_at": collected_at
    }

    announcements.append(item)


# =========================================================
# SAVE JSON
# =========================================================

with open(
    JSON_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        announcements,
        f,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# SAVE CSV
# =========================================================

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

    writer.writerows(
        announcements
    )


print(f"Saved JSON: {JSON_FILE}")

print(f"Saved CSV: {CSV_FILE}")


# =========================================================
# SAMPLE OUTPUT
# =========================================================

print("\nSample announcements:")

for item in announcements[:10]:

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
