import csv
import re
from pathlib import Path

INPUT_FILE = Path("data/research_priority.csv")
OUTPUT_FILE = Path("data/research_queue.csv")


# ============================================================
# 1. REMOVE NON-RESEARCH / SECURITY-LEVEL NOISE
# ============================================================

EXCLUDE_KEYWORDS = [
    # Mutual funds / ETFs
    "mutual fund",
    "mutual funds",
    "sbimf",
    "mf",
    "scheme",
    "idcw",
    "nav",
    "etf",
    "exchange traded fund",
    "portfolio",
    "fortnightly portfolio",

    # Debt/security-level announcements
    "commercial paper",
    "certificate of deposit",
    "non convertible debenture",
    "non-convertible debenture",
    "ncd",
    "debenture",
    "bond",
    "debt securities",

    # Routine security administration
    "interest payment",
    "redemption",
    "maturity",
    "principal repayment",
    "coupon payment",
    "record date for interest",
]


# ============================================================
# 2. IMPORTANT EVENTS WE WANT TO KEEP
# ============================================================

KEEP_EVENT_TYPES = [
    "Fund Raise",
    "Large Order",
    "Acquisition / Merger",
    "Capacity Expansion",
    "Regulatory Approval",
    "Strategic Partnership",
    "Promoter Activity",
    "Business Update",
    "Management Change",
    "Credit Rating",
    "Investor Communication",
    "Dividend / Buyback",
]


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_noise(row):
    """
    Identify announcements that are unlikely to be useful
    for equity research.
    """

    company = normalize(row.get("company", ""))
    headline = normalize(row.get("headline", ""))
    raw_text = normalize(row.get("raw_text", ""))

    text = f"{company} {headline} {raw_text}"

    for keyword in EXCLUDE_KEYWORDS:

        if keyword in text:
            return True

    return False


def announcement_key(row):
    """
    Create a key for detecting duplicate announcements.

    We primarily use company + headline because the same
    corporate announcement can appear under multiple
    security/scrip codes.
    """

    company = normalize(row.get("company", ""))

    headline = normalize(row.get("headline", ""))

    # Remove excessive punctuation
    headline = re.sub(r"[^a-z0-9₹ ]", " ", headline)

    headline = re.sub(r"\s+", " ", headline).strip()

    return f"{company}|{headline}"


def score_row(row):
    """
    Convert existing research score to an integer.
    """

    try:
        return int(row.get("research_score", 0))
    except (ValueError, TypeError):
        return 0


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
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    rows = list(reader)


print(f"Rows received: {len(rows)}")


# ============================================================
# STEP 1 — REMOVE NOISE
# ============================================================

clean_rows = []

removed_noise = 0

for row in rows:

    if is_noise(row):

        removed_noise += 1

        continue

    clean_rows.append(row)


print(
    f"Removed obvious noise: {removed_noise}"
)


# ============================================================
# STEP 2 — KEEP RELEVANT EVENTS
# ============================================================

relevant_rows = []

for row in clean_rows:

    event_type = row.get(
        "event_type",
        ""
    )

    priority = row.get(
        "priority",
        ""
    )

    # Keep only known research event types
    if event_type in KEEP_EVENT_TYPES:

        relevant_rows.append(row)

        continue

    # Also keep HIGH priority items
    if priority == "HIGH":

        relevant_rows.append(row)


print(
    f"Relevant rows before deduplication: "
    f"{len(relevant_rows)}"
)


# ============================================================
# STEP 3 — DEDUPLICATE
# ============================================================

unique_rows = {}

duplicates_removed = 0

for row in relevant_rows:

    key = announcement_key(row)

    if not key:
        continue

    if key not in unique_rows:

        unique_rows[key] = row

    else:

        duplicates_removed += 1

        existing = unique_rows[key]

        # Keep the row with the higher research score
        if score_row(row) > score_row(existing):

            unique_rows[key] = row


print(
    f"Duplicates removed: {duplicates_removed}"
)


# ============================================================
# STEP 4 — CONVERT TO LIST
# ============================================================

queue = list(unique_rows.values())


# ============================================================
# STEP 5 — SORT
# ============================================================

priority_rank = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
}


queue.sort(
    key=lambda row: (
        priority_rank.get(
            row.get("priority", "LOW"),
            3
        ),
        -score_row(row),
        row.get("published_date", "")
    )
)


# ============================================================
# STEP 6 — ADD RESEARCH STATUS
# ============================================================

for row in queue:

    row["research_status"] = "NEW"


# ============================================================
# STEP 7 — OUTPUT
# ============================================================

OUTPUT_FIELDS = [
    "unique_id",
    "source",
    "company",
    "scrip_code",
    "headline",
    "published_date",
    "url",
    "event_type",
    "priority",
    "research_score",
    "research_status",
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
        fieldnames=OUTPUT_FIELDS
    )

    writer.writeheader()

    for row in queue:

        writer.writerow({
            field: row.get(field, "")
            for field in OUTPUT_FIELDS
        })


# ============================================================
# SUMMARY
# ============================================================

high_count = sum(
    1
    for row in queue
    if row.get("priority") == "HIGH"
)

medium_count = sum(
    1
    for row in queue
    if row.get("priority") == "MEDIUM"
)


print()
print("==========================================")
print("RESEARCH QUEUE CREATED")
print("==========================================")

print(
    f"Input rows: {len(rows)}"
)

print(
    f"Noise removed: {removed_noise}"
)

print(
    f"Duplicates removed: {duplicates_removed}"
)

print(
    f"Final research queue: {len(queue)}"
)

print(
    f"HIGH priority: {high_count}"
)

print(
    f"MEDIUM priority: {medium_count}"
)

print(
    f"Saved: {OUTPUT_FILE}"
)


# ============================================================
# SHOW TOP 10
# ============================================================

print()
print("TOP RESEARCH ITEMS")

for row in queue[:10]:

    print("------------------------------------------")

    print(
        "Company:",
        row.get("company", "")
    )

    print(
        "Event:",
        row.get("event_type", "")
    )

    print(
        "Priority:",
        row.get("priority", "")
    )

    print(
        "Score:",
        row.get("research_score", "")
    )

    print(
        "Headline:",
        row.get("headline", "")
    )
