"""Targeted second extraction pass to fix label imbalance (see planning.md
Data collection plan). The first stratified-sampling pass came back 77%
Thorough among real takes -- Gatekeeping and Discouraging are genuinely
rare in this community, so this pass casts a wider net specifically for
hostile-toward-asker and vague-pessimism language, deduped against
candidates already in data/raw_candidates.csv.

Like extract_candidates.py, this produces raw UNLABELED candidates --
labeling is a separate manual step.
"""
import csv
import json
import random
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXTRACTED = DATA_DIR / "raw_cache" / "extracted"
CSV_PATH = DATA_DIR / "raw_candidates.csv"

MIN_LEN, MAX_LEN = 30, 500
SKIP_TEXT = {"[deleted]", "[removed]"}
SKIP_AUTHORS = {"AutoModerator", "[deleted]"}

GATEKEEPING_HINT = re.compile(
    r"\b(delusional|pathetic|cope+|embarrassing|cringe|clueless|laughable|"
    r"get real|wake up|conned|you.?re joking|no shot|no chance|"
    r"waste of (your )?(time|money)|ugly af|grow up|idiot|stupid|dumb(ass)?|"
    r"moron|loser|fucking (idiot|moron|stupid)|why (the|are you) (fuck|hell)|"
    r"lmao no\b|lol no\b)",
    re.I,
)
DISCOURAGING_HINT = re.compile(
    r"\b(probably (not|won.?t)|unlikely|low chance|slim chance|"
    r"wouldn.?t count on|not gonna happen|don.?t get your hopes up|"
    r"i.?d be surprised if|tough break|sorry to say|wouldn.?t hold my breath|"
    r"i wouldn.?t bother|not looking good)\b",
    re.I,
)

CAP_PER_BUCKET = 100


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        existing_ids = {row["id"] for row in csv.DictReader(f)}

    gk_candidates, dc_candidates = [], []

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

            is_gk = GATEKEEPING_HINT.search(text)
            is_dc = DISCOURAGING_HINT.search(text)
            if not (is_gk or is_dc):
                continue

            meta = row["meta"]
            candidate = {
                "id": row["id"],
                "type": "comment",
                "title": "",  # filled in below from conversations.json if needed
                "text": text,
                "score": meta.get("score", 0),
                "permalink": "https://reddit.com" + meta["permalink"],
                "label": "",
                "notes": "",
                "suggested_label": "",
                "suggested_reason": "",
                "_root": row["root"],
            }
            if is_gk and len(gk_candidates) < CAP_PER_BUCKET:
                gk_candidates.append(candidate)
            elif is_dc and len(dc_candidates) < CAP_PER_BUCKET:
                dc_candidates.append(candidate)

    # Fill in thread titles
    conversations = json.load(open(EXTRACTED / "conversations.json"))
    for c in gk_candidates + dc_candidates:
        c["title"] = clean(conversations.get(c["_root"], {}).get("title", ""))
        del c["_root"]

    random.seed(7)
    random.shuffle(gk_candidates)
    random.shuffle(dc_candidates)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "type", "title", "text", "score", "permalink", "label", "notes",
                      "suggested_label", "suggested_reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for c in gk_candidates + dc_candidates:
            writer.writerow(c)

    print(f"gatekeeping-hint candidates: {len(gk_candidates)}")
    print(f"discouraging-hint candidates: {len(dc_candidates)}")
    print(f"appended {len(gk_candidates) + len(dc_candidates)} new raw candidates to {CSV_PATH}")


if __name__ == "__main__":
    main()
