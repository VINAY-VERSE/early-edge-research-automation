import csv
import re
from pathlib import Path


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path("data/bse_announcements.csv")
OUTPUT_FILE = Path("data/bse_filtered.csv")


# ============================================================
# KEYWORDS
# ============================================================

HIGH_PRIORITY = {

    "Fund Raise": [
        "fund raise",
        "fundraising",
        "fund raising",
        "qip",
        "qualified institutional placement",
        "preferential issue",
        "preferential allotment",
        "rights issue",
        "private placement",
        "convertible",
        "warrants",
        "debenture",
        "equity shares"
    ],

    "Order Win": [
        "order",
        "orders",
        "purchase order",
        "work order",
        "letter of award",
        "loa",
        "contract",
        "contract award"
    ],

    "Acquisition / JV": [
        "acquisition",
        "acquire",
        "acquired",
        "merger",
        "amalgamation",
        "joint venture",
        "jv",
        "strategic partnership",
        "subsidiary"
    ],

    "Capacity Expansion": [
        "capacity expansion",
        "capacity addition",
        "expansion",
        "new plant",
        "new facility",
        "manufacturing facility",
        "commercial production",
        "commissioning",
        "capex"
    ],

    "Management Change": [
        "appointment",
        "appointed",
        "resignation",
        "resigned",
        "ceo",
        "chief executive",
        "cfo",
        "chief financial officer",
        "managing director",
        "whole time director"
    ],

    "Earnings": [
        "financial results",
        "financial result",
        "quarterly results",
        "annual results",
        "audited financial results",
        "unaudited financial results",
        "earnings"
    ],

    "Regulatory": [
        "approval",
        "regulatory approval",
        "license",
        "licence",
        "environmental clearance",
        "drug approval",
        "fda approval",
        " sebi ",
        " rbi "
    ]
}


# ============================================================
# LOW-PRIORITY / ROUTINE KEYWORDS
# ============================================================

LOW_PRIORITY = [

    "shareholding pattern",

    "investor complaints",

    "newspaper publication",

    "advertisement",

    "certificate under regulation",

    "compliance certificate",

    "reconciliation of share capital",

    "secretarial compliance",

    "loss of share certificate",

    "duplicate share certificate",

    "corporate governance",

    "annual return",

    "notice of annual general meeting",

    "postal ballot",

    "record date",

    "book closure",

    "closure of trading window"
]


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_announcement(text):

    text = text.lower()

    # ----------------------------------------
    # HIGH PRIORITY CATEGORIES
    # ----------------------------------------

    for category, keywords in HIGH_PRIORITY.items():

        for keyword in keywords:

            if keyword.lower() in text:

                return category, "HIGH"


    # ----------------------------------------
    # ROUTINE / LOW PRIORITY
    # ----------------------------------------

    for keyword in LOW_PRIORITY:

        if keyword.lower() in text:

            return "Routine / Compliance", "LOW"


    # ----------------------------------------
    # EVERYTHING ELSE
    # ----------------------------------------

    return "Other", "MEDIUM"


# ============================================================
# READ INPUT
# ============================================================

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    rows = list(reader)


print(
    f"Announcements read: {len(rows)}"
)


# ============================================================
# FILTER + CLASSIFY
# ============================================================

filtered_rows = []


for row in rows:

    company = row.get(
        "company",
        ""
    )

    headline = row.get(
        "headline",
        ""
    )

    raw_text = row.get(
        "raw_text",
        ""
    )

    combined_text = (
        f"{company} "
        f"{headline} "
        f"{raw_text}"
    )


    event_type, priority = classify_announcement(
        combined_text
    )


    # ----------------------------------------
    # Skip LOW priority announcements
    # ----------------------------------------

    if priority == "LOW":

        continue


    # ----------------------------------------
    # Add classification
    # ----------------------------------------

    row["event_type"] = event_type

    row["priority"] = priority

    filtered_rows.append(row)


# ============================================================
# SAVE OUTPUT
# ============================================================

output_fields = [

    "unique_id",

    "source",

    "company",

    "scrip_code",

    "headline",

    "published_date",

    "url",

    "raw_text",

    "collected_at",

    "event_type",

    "priority"
]


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=output_fields
    )

    writer.writeheader()

    for row in filtered_rows:

        writer.writerow({
            field: row.get(field, "")
            for field in output_fields
        })


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("ANNOUNCEMENT FILTER COMPLETE")
print("========================================")

print(
    f"Input announcements: {len(rows)}"
)

print(
    f"Filtered announcements: {len(filtered_rows)}"
)

print(
    f"Removed announcements: "
    f"{len(rows) - len(filtered_rows)}"
)

print(
    f"Saved: {OUTPUT_FILE}"
)


# ============================================================
# SAMPLE
# ============================================================

print("\nSample filtered announcements:")

for row in filtered_rows[:10]:

    print("--------------------------------")

    print(
        "Company:",
        row["company"]
    )

    print(
        "Event:",
        row["event_type"]
    )

    print(
        "Priority:",
        row["priority"]
    )

    print(
        "Headline:",
        row["headline"]
    )
