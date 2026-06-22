"""Third extraction pass, targeting Discouraging specifically (see
planning.md Data collection plan -- two prior passes left it at ~3% of
the non-SKIP pool). Two prior passes showed pessimism-keyword hits are
almost always actually Thorough once they cite any number/named school.
So this pass requires pessimism language AND the absence of any digit
in the comment -- a much sharper filter for genuine reasoning-free
pessimism.
"""
import csv
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXTRACTED = DATA_DIR / "raw_cache" / "extracted"
CSV_PATH = DATA_DIR / "raw_candidates.csv"

MIN_LEN, MAX_LEN = 25, 350
SKIP_TEXT = {"[deleted]", "[removed]"}
SKIP_AUTHORS = {"AutoModerator", "[deleted]"}

PESSIMISM = re.compile(
    r"\b(probably (not|won.?t)|unlikely|low chance|slim chance|"
    r"wouldn.?t count on|not gonna happen|don.?t get your hopes up|"
    r"i.?d be surprised if|tough (break|luck)|sorry to say|"
    r"wouldn.?t hold my breath|i wouldn.?t bother|not looking good|"
    r"slim to none|next to impossible|highly unlikely|no shot|no chance|"
    r"wouldn.?t bet on it)\b",
    re.I,
)
HAS_DIGIT = re.compile(r"\d")
CAP = 200


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        existing_ids = {row["id"] for row in csv.DictReader(f)}

    candidates = []
    with open(EXTRACTED / "utterances.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["id"] in existing_ids or row["reply_to"] is None:
                continue
            text = clean(row["text"])
            if text in SKIP_TEXT or row.get("user") in SKIP_AUTHORS:
                continue
            if not (MIN_LEN <= len(text) <= MAX_LEN):
                continue
            if HAS_DIGIT.search(text):
                continue
            if not PESSIMISM.search(text):
                continue

            meta = row["meta"]
            candidates.append({
                "id": row["id"],
                "type": "comment",
                "title": "",
                "text": text,
                "score": meta.get("score", 0),
                "permalink": "https://reddit.com" + meta["permalink"],
                "label": "",
                "notes": "",
                "suggested_label": "",
                "suggested_reason": "",
                "_root": row["root"],
            })
            if len(candidates) >= CAP:
                break

    conversations = json.load(open(EXTRACTED / "conversations.json"))
    for c in candidates:
        c["title"] = clean(conversations.get(c["_root"], {}).get("title", ""))
        del c["_root"]

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "type", "title", "text", "score", "permalink", "label", "notes",
                      "suggested_label", "suggested_reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for c in candidates:
            writer.writerow(c)

    print(f"appended {len(candidates)} no-digit pessimism candidates to {CSV_PATH}")


if __name__ == "__main__":
    main()
