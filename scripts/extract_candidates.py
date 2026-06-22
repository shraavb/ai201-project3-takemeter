"""Pull candidate posts/comments for TakeMeter labeling from the
ConvoKit ApplyingToCollege corpus (academic Reddit research dataset,
http://zissou.infosci.cornell.edu/convokit/datasets/subreddit-corpus/).

Source data lives in data/raw_cache/extracted/ (utterances.jsonl,
conversations.json) -- not committed to git, see README for how to
re-fetch it.

This script does NOT assign labels. It builds a raw candidate pool,
stratified by a rough keyword heuristic so the pool isn't 90% generic
small talk, for a human to read and label afterward.
"""
import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXTRACTED = DATA_DIR / "raw_cache" / "extracted"
OUT_PATH = DATA_DIR / "raw_candidates.csv"

MIN_LEN = 40
SKIP_TEXT = {"[deleted]", "[removed]"}
SKIP_AUTHORS = {"AutoModerator", "[deleted]"}

# Rough heuristics used only to stratify sampling -- NOT the real label.
# Real labeling is a human judgment call against the decision rule in
# planning.md.
HEURISTICS = {
    "gatekeeping_hint": re.compile(
        r"\b(lol|lmao|no shot|no chance|delusional|cope|waste of (time|money)|"
        r"not (a )?real |unless you (go|got)|non-?target|joke)\b", re.I
    ),
    "thorough_hint": re.compile(
        r"\b(\d\.\d{1,2}\s*gpa|\d{3,4}\s*sat|\d{2}\s*act|gpa of|class of \d{4}|"
        r"i got into|i was accepted|i applied to|admitted to|rejected from)\b", re.I
    ),
    "discouraging_hint": re.compile(
        r"\b(probably (not|won'?t)|wouldn'?t (bother|count)|unlikely|i doubt|"
        r"low chance|slim chance|not looking good)\b", re.I
    ),
}
CAP_PER_BUCKET = 110
TOTAL_CAP = 420


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def bucket_for(text: str) -> str:
    for name, pattern in HEURISTICS.items():
        if pattern.search(text):
            return name
    return "generic_hint"


def main():
    conversations = json.load(open(EXTRACTED / "conversations.json"))

    posts = {}  # id -> dict
    comment_rows = []

    with open(EXTRACTED / "utterances.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            text = clean(row["text"])
            user = row.get("user")
            if text in SKIP_TEXT or user in SKIP_AUTHORS or len(text) < MIN_LEN:
                continue

            is_post = row["reply_to"] is None and row["id"] == row["root"]
            is_top_level_comment = row["reply_to"] == row["root"] and not is_post

            if is_post:
                meta = conversations.get(row["id"], {})
                posts[row["id"]] = {
                    "id": row["id"],
                    "type": "post",
                    "title": clean(meta.get("title", "")),
                    "text": text,
                    "score": meta.get("gilded", row["meta"].get("score", 0)),
                    "permalink": "https://reddit.com" + row["meta"]["permalink"],
                }
            elif is_top_level_comment:
                meta = conversations.get(row["root"], {})
                comment_rows.append({
                    "id": row["id"],
                    "type": "comment",
                    "title": clean(meta.get("title", "")),
                    "text": text,
                    "score": row["meta"].get("score", 0),
                    "permalink": "https://reddit.com" + row["meta"]["permalink"],
                })

    # Stratified sample: bucket comments by heuristic hint, cap per bucket
    # so rarer patterns (gatekeeping/thorough) aren't drowned out by the
    # much larger generic bucket, then shuffle.
    buckets = defaultdict(list)
    for row in comment_rows:
        buckets[bucket_for(row["text"])].append(row)

    random.seed(42)
    sampled = []
    for name, rows in buckets.items():
        random.shuffle(rows)
        sampled.extend(rows[:CAP_PER_BUCKET])

    # Mix in post candidates with substantial selftext (some "chance me"
    # posts ARE the take, e.g. self-assessment before asking for feedback).
    post_candidates = [p for p in posts.values() if len(p["text"]) >= 80]
    random.shuffle(post_candidates)
    sampled.extend(post_candidates[:60])

    random.shuffle(sampled)
    sampled = sampled[:TOTAL_CAP]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "type", "title", "text", "score", "permalink", "label"])
        writer.writeheader()
        for row in sampled:
            row["label"] = ""
            writer.writerow(row)

    print(f"posts indexed: {len(posts)}, top-level comments seen: {len(comment_rows)}")
    print(f"bucket sizes (pre-cap): " + ", ".join(f"{k}={len(v)}" for k, v in buckets.items()))
    print(f"Wrote {len(sampled)} candidates to {OUT_PATH}")


if __name__ == "__main__":
    main()
