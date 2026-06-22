"""One-time merge of Claude-generated pre-label suggestions (data/suggestions_batch*.json)
into data/raw_candidates.csv as suggested_label/suggested_reason columns.

Disclosed in planning.md AI Tool Plan: Claude (not the Groq baseline model)
pre-labeled the full remaining candidate pool by applying the decision rule
in planning.md. Every suggestion is reviewed and can be overridden in
scripts/annotate.py -- nothing here is a final label.
"""
import csv
import glob
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "raw_candidates.csv"


def main():
    suggestions = {}
    for path in sorted(glob.glob(str(DATA_DIR / "suggestions_batch*.json"))):
        with open(path, encoding="utf-8") as f:
            suggestions.update(json.load(f))

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = ["id", "type", "title", "text", "score", "permalink", "label", "notes",
                  "suggested_label", "suggested_reason"]

    matched = 0
    for row in rows:
        sug = suggestions.get(row["id"])
        if sug:
            row["suggested_label"] = sug[0]
            row["suggested_reason"] = sug[1]
            matched += 1
        else:
            row.setdefault("suggested_label", "")
            row.setdefault("suggested_reason", "")

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    already_labeled = sum(1 for r in rows if r["label"])
    unlabeled_no_suggestion = sum(1 for r in rows if not r["label"] and not r["suggested_label"])
    print(f"total rows: {len(rows)}")
    print(f"already labeled (untouched): {already_labeled}")
    print(f"suggestions applied: {matched}")
    print(f"unlabeled with NO suggestion (will show with no hint): {unlabeled_no_suggestion}")


if __name__ == "__main__":
    main()
