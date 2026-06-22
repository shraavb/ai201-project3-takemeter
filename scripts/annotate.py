"""Interactive CLI for hand-labeling data/raw_candidates.csv against the
4-label decision rule in planning.md.

Each row carries a suggested_label/suggested_reason pre-filled by Claude
(disclosed in planning.md AI Tool Plan -- NOT the Groq baseline model, to
keep the baseline comparison independent). Press Enter to accept the
suggestion, or type a number to override it. Every row still requires an
explicit keypress -- nothing is auto-accepted in bulk. Final agreement
rate with the suggestions can be computed afterward by comparing the
label column against suggested_label.

Run it, label what you can, quit anytime (q) -- progress is saved to
disk after every single annotation, so re-running picks up where you
left off (rows already labeled or skipped are not re-shown).
"""
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_candidates.csv"

LABELS = {
    "1": "Gatekeeping",
    "2": "Thorough",
    "3": "Discouraging",
    "4": "Generic",
}

RULE_REMINDER = """\
Decision rule (first match wins):
  1) Gatekeeping     hostile/mocking toward the ASKER specifically
  2) Thorough        not hostile, has real specifics (numbers/named outcomes/real tradeoffs)
  3) Discouraging     not hostile, not specific, pessimistic
  4) Generic         everything else (platitudes, vague cheerleading)
  s) skip            not an opinion/take at all (pure question, joke, off-topic, [deleted])
  q) quit (saves progress)
  [Enter] accept the suggested label shown for this row
"""


def load_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def save_rows(rows, fieldnames):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_distribution(rows):
    counts = {}
    labeled_total = 0
    for r in rows:
        lbl = r["label"]
        if lbl and lbl != "SKIP":
            counts[lbl] = counts.get(lbl, 0) + 1
            labeled_total += 1
    skipped = sum(1 for r in rows if r["label"] == "SKIP")
    remaining = sum(1 for r in rows if not r["label"])
    print(f"\nlabeled={labeled_total} skipped={skipped} remaining={remaining}")
    if labeled_total:
        for name in ("Gatekeeping", "Thorough", "Discouraging", "Generic"):
            n = counts.get(name, 0)
            pct = 100 * n / labeled_total
            print(f"  {name:14s} {n:4d}  ({pct:.0f}%)")


def main():
    rows, fieldnames = load_rows()
    print(RULE_REMINDER)
    print_distribution(rows)

    for i, row in enumerate(rows):
        if row["label"]:
            continue

        print("\n" + "=" * 70)
        if row["title"]:
            print(f"[{row['type']}] THREAD: {row['title']}")
        print(f"TEXT: {row['text']}")
        print(f"(score={row['score']}  {row['permalink']})")
        if row["suggested_label"]:
            print(f"\nsuggested: {row['suggested_label']} -- {row['suggested_reason']}")

        prompt = "\nlabel [1=Gatekeeping 2=Thorough 3=Discouraging 4=Generic s=skip q=quit"
        prompt += ", Enter=accept suggestion]: " if row["suggested_label"] else "]: "

        while True:
            choice = input(prompt).strip().lower()
            if choice == "" and row["suggested_label"]:
                row["label"] = row["suggested_label"]
                break
            if choice == "q":
                save_rows(rows, fieldnames)
                print_distribution(rows)
                print("Progress saved.")
                return
            if choice == "s":
                row["label"] = "SKIP"
                break
            if choice in LABELS:
                row["label"] = LABELS[choice]
                break
            print("invalid input, try again")

        note = input("note on this one, if it gave you pause (enter to skip): ").strip()
        row["notes"] = note

        save_rows(rows, fieldnames)
        print_distribution(rows)

    print("\nAll candidates labeled or skipped.")


if __name__ == "__main__":
    main()
