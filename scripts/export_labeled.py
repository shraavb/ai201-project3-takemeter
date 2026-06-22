"""Export the final text,label,notes CSV for the fine-tuning notebook
from data/raw_candidates.csv (the working annotation file, which keeps
extra columns -- title/score/permalink -- useful during labeling but
not needed by the notebook).

Drops unlabeled and SKIP ("not an opinion/take") rows.
"""
import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SRC = DATA_DIR / "raw_candidates.csv"
OUT = DATA_DIR / "labeled_dataset.csv"


def main():
    with open(SRC, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    labeled = [r for r in rows if r["label"] and r["label"] != "SKIP"]

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        for r in labeled:
            writer.writerow({"text": r["text"], "label": r["label"], "notes": r["notes"]})

    counts = Counter(r["label"] for r in labeled)
    total = len(labeled)
    print(f"Wrote {total} labeled examples to {OUT}")
    for label, n in counts.most_common():
        print(f"  {label:14s} {n:4d}  ({100*n/total:.0f}%)")
    if total < 200:
        print(f"\nWARNING: only {total} labeled -- need at least 200.")
    for label, n in counts.items():
        if n / total > 0.7:
            print(f"\nWARNING: {label} is {100*n/total:.0f}% of the dataset -- over the 70% imbalance threshold.")


if __name__ == "__main__":
    main()
