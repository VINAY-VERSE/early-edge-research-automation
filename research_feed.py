import csv
import re
from pathlib import Path


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = Path("data/bse_filtered.csv")
OUTPUT_FILE = Path("data/research_feed.csv")


# ============================================================
# RESEARCH EVENT KEYWORDS
# ============================================================

EVENT_KEYWORDS = {

    "Fund Raise": [
        "fund raise",
        "fundraise",
        "fund raising",
        "fundraising",
        "preferential issue",
        "preferential allotment",
        "rights issue",
        "qualified institutional placement",
        "qip",
        "private placement",
        "follow-on public offer",
        "fpo",
        "public issue",
        "issue of shares",
        "issue of equity",
        "issue of securities",
        "convertible",
        "warrant",
        "debenture",
        "debt raise",
        "capital raise",
        "raising of funds",
    ],

    "Large Order": [
        "order worth",
        "order of rs",
        "order of ₹",
        "order worth rs",
        "order worth inr",
        "received order",
        "received orders",
        "new order",
        "new orders",
        "purchase order",
        "work order",
        "letter of award",
        "loa",
        "contract worth",
        "contract of rs",
        "contract value",
        "bagged order",
        "bagged orders",
        "secured order",
        "secured orders",
    ],

    "Capacity Expansion": [
        "capacity expansion",
        "capacity addition",
        "capacity increase",
        "expansion of capacity",
        "new capacity",
        "installed capacity",
        "commissioned capacity",
        "capacity enhancement",
        "expansion project",
        "new plant",
        "new facility",
        "manufacturing facility",
        "production capacity",
    ],

    "Capex / Project": [
        "capital expenditure",
        "capex",
        "capital investment",
        "investment of rs",
        "investment of ₹",
        "investment in",
        "project cost",
        "project investment",
        "new project",
        "greenfield",
        "brownfield",
        "plant expansion",
        "plant commissioning",
        "commercial production",
    ],

    "Acquisition / Merger": [
        "acquisition",
        "acquire",
        "acquired",
        "takeover",
        "merger",
        "amalgamation",
        "scheme of arrangement",
        "business transfer",
        "purchase of stake",
        "acquisition of stake",
        "stake acquisition",
        "subsidiary acquisition",
    ],

    "Strategic Partnership": [
        "strategic partnership",
        "strategic alliance",
        "joint venture",
        "joint venture agreement",
        "partnership agreement",
        "memorandum of understanding",
        "mou",
        "collaboration",
        "strategic collaboration",
        "technology partnership",
    ],

    "Promoter Activity": [
        "promoter purchase",
        "promoter acquisition",
        "promoter selling",
        "promoter sale",
        "promoter group",
        "inter-se transfer",
        "promoter holding",
        "shares acquired by promoter",
        "shares sold by promoter",
    ],

    "Regulatory Approval": [
        "approval received",
        "regulatory approval",
        "approved by",
        "approval from",
        "drug approval",
        "usfda approval",
        "usfda",
        "fda approval",
        "dcgi approval",
        "ema approval",
        "regulatory clearance",
        "license received",
        "licence received",
    ],

    "New Product / Launch": [
        "new product",
        "product launch",
        "launched",
        "launches",
        "commercial launch",
        "new product launch",
        "new molecule",
        "new technology",
        "new platform",
    ],

    "Management Change": [
        "appointment of",
        "appointed as",
        "resignation of",
        "resigned as",
        "change in director",
        "change in management",
        "new ceo",
        "new cfo",
        "chief executive officer",
        "chief financial officer",
        "managing director",
        "whole time director",
    ],

    "Business Update": [
        "business update",
        "business performance",
        "operational update",
        "production update",
        "sales update",
        "monthly sales",
        "production volume",
        "sales volume",
    ],
}


# ============================================================
# LOW-VALUE / NOISE KEYWORDS
# ============================================================

NOISE_KEYWORDS = [
    "newspaper advertisement",
    "loss of share certificate",
    "duplicate share certificate",
    "investor grievance",
    "investor complaints",
    "closure of trading window",
    "trading window",
    "record date",
    "book closure",
    "notice of agm",
    "notice of egm",
    "agm notice",
    "egm notice",
    "postal ballot",
    "scrutinizer",
    "voting results",
    "shareholding pattern",
    "corporate governance",
    "secretarial audit",
    "compliance certificate",
    "certificate under regulation",
    "related party transaction",
    "reconciliation of share capital",
    "listing fees",
    "annual return",
]


# ============================================================
# HIGH PRIORITY CATEGORIES
# ============================================================

HIGH_PRIORITY = {
    "Fund Raise",
    "Large Order",
    "Capacity Expansion",
    "Capex / Project",
    "Acquisition / Merger",
    "Regulatory Approval",
    "Promoter Activity",
}


MEDIUM_PRIORITY = {
    "Strategic Partnership",
    "New Product / Launch",
    "Management Change",
    "Business Update",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_text(text):
    """
    Convert text to lowercase and remove excessive whitespace.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_keyword(text, keyword):
    """
    Check whether keyword exists in text.
    """
    return keyword.lower() in text


def classify_event(headline, raw_text):
    """
    Determine the research event category.
    """

    text = normalize_text(f"{headline} {raw_text}")

    # First remove obvious low-value announcements
    for noise in NOISE_KEYWORDS:
        if noise in text:
            return "Noise"

    # Check important categories
    for category, keywords in EVENT_KEYWORDS.items():

        for keyword in keywords:

            if contains_keyword(text, keyword):
                return category

    return "Other"


def assign_priority(event_type):
    """
    Assign research priority.
    """

    if event_type in HIGH_PRIORITY:
        return "HIGH"

    if event_type in MEDIUM_PRIORITY:
        return "MEDIUM"

    if event_type == "Noise":
        return "LOW"

    return "LOW"


def calculate_research_score(event_type, headline, raw_text):
    """
    Simple rule-based research score from 0-100.
    """

    score = 0

    if event_type in HIGH_PRIORITY:
        score += 70

    elif event_type in MEDIUM_PRIORITY:
        score += 40

    else:
        score += 10

    text = normalize_text(f"{headline} {raw_text}")

    # Monetary value mentioned
    money_patterns = [
        r"₹\s*\d+",
        r"rs\.?\s*\d+",
        r"inr\s*\d+",
        r"\d+\s*crore",
        r"\d+\s*cr",
        r"\d+\s*million",
        r"\d+\s*billion",
    ]

    for pattern in money_patterns:

        if re.search(pattern, text):
            score += 15
            break

    # Capacity / volume numbers
    numeric_keywords = [
        "mt",
        "million tonnes",
        "million units",
        "mw",
        "gw",
        "units",
        "capacity",
    ]

    for keyword in numeric_keywords:

        if keyword in text:
            score += 5
            break

    # Cap at 100
    return min(score, 100)


# ============================================================
# MAIN PROCESS
# ============================================================

print("Starting research feed generation...")

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)

    rows = list(reader)


print(f"Records read from filtered file: {len(rows)}")


research_rows = []


for row in rows:

    headline = row.get("headline", "")
    raw_text = row.get("raw_text", "")

    event_type = classify_event(
        headline,
        raw_text
    )

    priority = assign_priority(
        event_type
    )

    research_score = calculate_research_score(
        event_type,
        headline,
        raw_text
    )

    # Keep HIGH and MEDIUM priority announcements
    if priority not in {"HIGH", "MEDIUM"}:
        continue

    new_row = dict(row)

    new_row["event_type"] = event_type
    new_row["priority"] = priority
    new_row["research_score"] = research_score

    research_rows.append(new_row)


# ============================================================
# SORT
# ============================================================

priority_order = {
    "HIGH": 0,
    "MEDIUM": 1
}


research_rows.sort(
    key=lambda x: (
        priority_order.get(
            x.get("priority", "MEDIUM"),
            2
        ),
        -int(x.get("research_score", 0))
    )
)


# ============================================================
# OUTPUT
# ============================================================

if research_rows:

    fieldnames = list(research_rows[0].keys())

else:

    fieldnames = [
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
        "priority",
        "research_score",
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
    writer.writerows(research_rows)


# ============================================================
# SUMMARY
# ============================================================

high_count = sum(
    1
    for row in research_rows
    if row["priority"] == "HIGH"
)

medium_count = sum(
    1
    for row in research_rows
    if row["priority"] == "MEDIUM"
)


print("----------------------------------------")
print("Research feed generated successfully")
print("----------------------------------------")

print(f"Total filtered announcements: {len(rows)}")
print(f"Research announcements: {len(research_rows)}")
print(f"HIGH priority: {high_count}")
print(f"MEDIUM priority: {medium_count}")

print(f"\nSaved file:")
print(OUTPUT_FILE)

print("\nTop research announcements:")

for item in research_rows[:10]:

    print("----------------------------------------")
    print("Company:", item["company"])
    print("Event:", item["event_type"])
    print("Priority:", item["priority"])
    print("Score:", item["research_score"])
    print("Headline:", item["headline"])
