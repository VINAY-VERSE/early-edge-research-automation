import csv
import re
from pathlib import Path

INPUT_FILE = Path("data/research_feed.csv")
OUTPUT_FILE = Path("data/research_priority.csv")


# ---------------------------------------------------------
# EVENT KEYWORDS
# ---------------------------------------------------------

HIGH_PRIORITY = {
    "Fund Raise": [
        "fund raise",
        "fundraise",
        "qip",
        "preferential issue",
        "preferential allotment",
        "rights issue",
        "qualified institutional",
        "private placement",
        "issue of shares",
        "issue of equity",
        "capital raise",
    ],

    "Large Order": [
        "order worth",
        "order received",
        "order secured",
        "order book",
        "work order",
        "contract worth",
        "letter of award",
        "loa",
        "purchase order",
    ],

    "Acquisition / Merger": [
        "acquisition",
        "acquire",
        "acquired",
        "merger",
        "amalgamation",
        "takeover",
    ],

    "Capacity Expansion": [
        "capacity expansion",
        "capacity addition",
        "new capacity",
        "expansion project",
        "new plant",
        "new facility",
        "commissioning",
        "commercial production",
    ],

    "Regulatory Approval": [
        "approval received",
        "regulatory approval",
        "usfda approval",
        "usfda",
        "ema approval",
        "dcgi approval",
        "drug approval",
        "final approval",
    ],

    "Strategic Partnership": [
        "strategic partnership",
        "strategic agreement",
        "joint venture",
        "jv",
        "partnership",
        "collaboration",
        "technology agreement",
    ],

    "Promoter Activity": [
        "promoter acquisition",
        "promoter purchase",
        "promoter buying",
        "promoter stake",
        "promoter holding",
        "pledge",
    ],
}


MEDIUM_PRIORITY = {
    "Business Update": [
        "business update",
        "operational update",
        "business performance",
        "monthly update",
        "production update",
        "sales update",
    ],

    "Management Change": [
        "appointment",
        "resignation",
        "appointed",
        "director",
        "chief executive",
        "ceo",
        "cfo",
        "key managerial",
    ],

    "Credit Rating": [
        "credit rating",
        "rating reaffirmed",
        "rating upgrade",
        "rating downgrade",
        "icra",
        "crisil",
        "care ratings",
    ],

    "Investor Communication": [
        "investor presentation",
        "analyst meet",
        "investor meet",
        "conference call",
        "earnings call",
    ],

    "Dividend / Buyback": [
        "dividend",
        "buyback",
        "bonus issue",
        "stock split",
    ],
}


LOW_VALUE_KEYWORDS = [
    "mutual fund",
    "scheme",
    "idcw",
    "nav",
    "portfolio",
    "daily nav",
    "fortnightly portfolio",
    "monthly nav",
]


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def normalize(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def find_event(headline):
    text = normalize(headline)

    # Remove obvious low-value mutual fund noise
    for keyword in LOW_VALUE_KEYWORDS:
        if keyword in text:
            return "Other", "LOW"

    # High priority events
    for event_type, keywords in HIGH_PRIORITY.items():
        for keyword in keywords:
            if keyword in text:
                return event_type, "HIGH"

    # Medium priority events
    for event_type, keywords in MEDIUM_PRIORITY.items():
        for keyword in keywords:
            if keyword in text:
                return event_type, "MEDIUM"

    return "Other", "LOW"


# ---------------------------------------------------------
# READ INPUT
# ---------------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)


print(f"Rows received: {len(rows)}")


# ---------------------------------------------------------
# CLASSIFY
# ---------------------------------------------------------

output_rows = []

for row in rows:

    headline = row.get("headline", "")

    event_type, priority = find_event(headline)

    output_rows.append({
        "unique_id": row.get("unique_id", ""),
        "source": row.get("source", ""),
        "company": row.get("company", ""),
        "scrip_code": row.get("scrip_code", ""),
        "headline": headline,
        "published_date": row.get("published_date", ""),
        "url": row.get("url", ""),
        "event_type": event_type,
        "priority": priority,
        "raw_text": row.get("raw_text", ""),
        "collected_at": row.get("collected_at", ""),
    })


# ---------------------------------------------------------
# SORT
# ---------------------------------------------------------

priority_rank = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
}

output_rows.sort(
    key=lambda x: (
        priority_rank.get(x["priority"], 3),
        x["published_date"]
    ),
    reverse=False
)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(exist_ok=True)

fieldnames = [
    "unique_id",
    "source",
    "company",
    "scrip_code",
    "headline",
    "published_date",
    "url",
    "event_type",
    "priority",
    "raw_text",
    "collected_at",
]


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(output_rows)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

high = sum(
    1 for x in output_rows
    if x["priority"] == "HIGH"
)

medium = sum(
    1 for x in output_rows
    if x["priority"] == "MEDIUM"
)

low = sum(
    1 for x in output_rows
    if x["priority"] == "LOW"
)


print(f"Saved: {OUTPUT_FILE}")
print(f"HIGH: {high}")
print(f"MEDIUM: {medium}")
print(f"LOW: {low}")
