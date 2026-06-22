"""Curate the full 820-row mined pool (data/raw_candidates.csv) down to a
balanced ~220-candidate set for human review via annotate.py.

Keeps every already-confirmed human label, keeps every Gatekeeping/
Discouraging suggestion (genuinely rare in this corpus -- see planning.md),
and subsamples the abundant Thorough/Generic suggestions down so Thorough
stays under the assignment's 70% imbalance ceiling. SKIP-suggested rows
are dropped entirely -- they were already determined out of scope.

The full unfiltered pool is archived to data/raw_candidates_full_pool.csv
in case more rare-label examples are needed later.
"""
import csv
import random
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "raw_candidates.csv"
ARCHIVE_PATH = DATA_DIR / "raw_candidates_full_pool.csv"

TARGET_THOROUGH = 130
TARGET_GENERIC = 54

random.seed(99)


def eff_label(row):
    return row["label"] if row["label"] else row["suggested_label"]


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        fieldnames = csv.DictReader(f).fieldnames
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    shutil.copy(CSV_PATH, ARCHIVE_PATH)

    already_confirmed = [r for r in rows if r["label"]]
    unconfirmed = [r for r in rows if not r["label"]]

    by_suggestion = {"Gatekeeping": [], "Discouraging": [], "Thorough": [], "Generic": []}
    for r in unconfirmed:
        if r["suggested_label"] in by_suggestion:
            by_suggestion[r["suggested_label"]].append(r)

    confirmed_counts = {}
    for r in already_confirmed:
        confirmed_counts[r["label"]] = confirmed_counts.get(r["label"], 0) + 1

    random.shuffle(by_suggestion["Thorough"])
    random.shuffle(by_suggestion["Generic"])

    n_thorough = max(0, TARGET_THOROUGH - confirmed_counts.get("Thorough", 0))
    n_generic = max(0, TARGET_GENERIC - confirmed_counts.get("Generic", 0))

    curated = (
        already_confirmed
        + by_suggestion["Gatekeeping"]
        + by_suggestion["Discouraging"]
        + by_suggestion["Thorough"][:n_thorough]
        + by_suggestion["Generic"][:n_generic]
    )
    random.shuffle(curated)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(curated)

    print(f"Archived full pool ({len(rows)} rows) to {ARCHIVE_PATH}")
    print(f"Curated pool: {len(curated)} rows in {CSV_PATH}")
    from collections import Counter
    print(Counter(eff_label(r) for r in curated))


if __name__ == "__main__":
    main()
