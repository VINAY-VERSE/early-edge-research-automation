import feedparser
import requests
import json
import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

BSE_RSS_URL = "https://beta.bseindia.com/data/xml/announcements.xml"

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

JSON_FILE = OUTPUT_DIR / "bse_announcements.json"
CSV_FILE = OUTPUT_DIR / "bse_announcements.csv"


def extract_scrip_code(title):
    match = re.search(r"\((\d{6})\)", title)
    return match.group(1) if match else ""


def extract_company_name(title):
    match = re.match(r"^(.*?)\s*\(\d{6}\)", title)
    return match.group(1).strip() if match else title.strip()


def create_unique_id(url, title):
    value = f"BSE|{url}|{title}"
    return hashlib.sha256(value.encode()).hexdigest()[:16]


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
    description = entry.get("description", "").strip()
    published = entry.get("published", "").strip()

    company = extract_company_name(title)
    scrip_code = extract_scrip_code(title)

    unique_id = create_unique_id(url, title)

    collected_at = datetime.now(timezone.utc).isoformat()

    item = {
        "unique_id": unique_id,
        "source": "BSE",
        "company": company,
        "scrip_code": scrip_code,
        "headline": title,
        "published_date": published,
        "url": url,
        "raw_text": description,
        "collected_at": collected_at
    }

    announcements.append(item)

with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(
        announcements,
        f,
        ensure_ascii=False,
        indent=2
    )

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

with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(announcements)

print(f"Saved JSON: {JSON_FILE}")
print(f"Saved CSV: {CSV_FILE}")

print("\nSample announcements:")

for item in announcements[:5]:
    print("--------------------------------")
    print("Company:", item["company"])
    print("Scrip:", item["scrip_code"])
    print("Headline:", item["headline"])
    print("Date:", item["published_date"])
    print("URL:", item["url"])
