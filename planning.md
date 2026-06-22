# TakeMeter Planning — r/ApplyingToCollege (A2C) Discourse Quality

## Community
r/ApplyingToCollege (A2C) — college applicants and admitted students. Recurring thread types: "chance me" admissions assessments, school-choice debates, stats/GPA/SAT comparisons, application-strategy questions.

**Why this community / why these labels matter:** A2C is high-volume and high-stakes for its users — every "chance me" thread mixes genuinely useful, specific feedback with empty cheerleading and outright elitist dismissal, and regulars in the community actively complain about both ("this sub is just gatekeeping" / "stop with the generic good-luck spam"). The Gatekeeping/Thorough/Discouraging/Generic distinction maps directly onto what an A2C regular already recognizes as the difference between a reply worth reading and one worth scrolling past.

(Originally scoped to r/MBA — pivoted here because r/MBA isn't in any pre-collected research corpus, and Reddit's current Data API Terms / "Responsible Builder Policy" explicitly prohibit using Reddit data to train ML models without written approval, which blocks live scraping via PRAW for this project regardless of collection method. A2C runs on the same discourse pattern as r/MBA's "chance me" culture — admissions self-assessment, elitism about top schools, generic reassurance, stats-based feedback — so the taxonomy below ported over with a vocabulary swap (GMAT/M7/non-target → SAT/GPA/T20/Ivy) rather than a redesign.)

## Data source and provenance
Source: [ConvoKit Reddit Corpus (by subreddit)](https://convokit.cornell.edu/documentation/subreddit.html), built by Cornell's Social Dynamics Lab from a 2019 Pushshift snapshot, explicitly distributed for non-commercial NLP research. Downloaded `ApplyingToCollege.corpus.zip` (148MB compressed) directly — not via Reddit's live API, sidestepping the current ToS restriction on live scraping for ML training.

- Corpus stats: 121,007 posts, 1,027,292 comments, 53,067 users, subreddit-wide (not date-filtered; spans roughly 2016–2019 based on sampled timestamps).
- Raw files cached locally at `data/raw_cache/` (gitignored — too large to commit; re-fetch via the URL above + `unzip`).
- Extraction script: `scripts/extract_candidates.py` streams `utterances.jsonl`, keeps top-level comments and posts with substantial selftext, filters `[deleted]`/`[removed]`/AutoModerator/short stubs, and stratifies sampling by a rough keyword heuristic (gatekeeping/thorough/discouraging/generic hints) so the candidate pool isn't 90% generic small talk. The heuristic is sampling scaffolding only — it is NOT the label; every candidate still gets read and labeled by hand against the decision rule below.
- Output: `data/raw_candidates.csv`, 420 raw candidates, unlabeled.

## Unit of analysis
Mix of posts and top-level comments. In scope: any text that states an opinion/take (a chance assessment, a school recommendation, stats-based feedback, an admissions-strategy take). Out of scope: pure questions with no opinion content, jokes/anecdotes with no actual take (e.g. "I had a dream I got into Yale without even applying") — excluded during annotation, never labeled.

## Label taxonomy (4 labels)

Two conceptual axes (substance: specific vs vague; tone: hostile vs not) collapsed into one decision rule, checked top to bottom — first match wins, so every example gets exactly one label:

1. **Gatekeeping** — dismissive, mocking, or elitist; attacks the asker's legitimacy/credentials directly, not just the system or colleges in general. Hostility toward the asker wins regardless of whether specifics are also present.
2. **Thorough** — not hostile to the asker, and backed by specific reasoning: numbers (GPA/SAT/ACT), named schools/outcomes, real tradeoffs, relevant personal experience, or genuinely informative explanation. Conclusion can be positive or negative.
3. **Discouraging** — not hostile, not specific enough to qualify as Thorough, and the take is pessimistic with no real reasoning given.
4. **Generic** — everything else: platitudes, cheerleading, vague evaluative language ("great GPA," "looks good") with no concrete numbers or comparisons, advice that could be pasted onto nearly any post.

Decision rule, restated as a check order:
- Hostile/mocking toward the asker specifically? → **Gatekeeping**. (Cynicism about colleges/the system in general does NOT count — see Discouraging uncertain case below.)
- Else, specific (numbers, named outcomes, real tradeoffs, genuine explanation)? → **Thorough**.
- Else, pessimistic? → **Discouraging**.
- Else → **Generic**.

## Examples (real quotes from the corpus)

### Gatekeeping
1. *"No, honestly, that's pathetic. I'll have the Ivy League brand to back me up when I graduate. I'm sure that they'd drop you as an associate really quickly if they found out that you conned your way in."* — direct insult, no real reasoning.
2. *"Just make sure you're not ugly af. And if you are, get real good at photoshop in the next few hours."* — mocking, zero substance.
3. **Uncertain case:** *"...compared to the personal statement, it isn't the big dog that it is at state schools especially at 2230. Even HMC's average is below that. There is no need to worry about it. If you think 70 points will make that big of a deal, you're delusional."* — has real specifics (named school, score comparison) AND a direct insult ("you're delusional"). Decision: **Gatekeeping** — hostility toward the asker outranks specificity in the check order, even when the reasoning is otherwise sound.

### Thorough
1. *"I got into dgs with a 1370 SAT... DGS is the easiest major to get admitted into. My GPA was a 3.18 UW."* — concrete personal data point.
2. *"700 on math is 66th percentile. That's like a 650 on US History or Literature. If your school requires subject tests, send it..."* — specific, conditional reasoning.
3. **Uncertain case:** *"Your GPA/Location is going to hold you back at top schools. Colleges compare you to kids from your school and they review applications on a regional basis... a 3.5 won't cut it..."* — reads as blunt/negative (sounds like it should be Discouraging), but it's not hostile to the asker and gives real, specific reasoning (regional comparison logic). Decision: **Thorough** — specificity beats pessimism in the check order; a well-reasoned negative take is still Thorough, not Discouraging.

### Discouraging
1. *"Probably won't get paid though."* (re: journalism internships) — flat pessimism, no reasoning given.
2. *"It's a pretty good thing to put on your resume but don't count on it making a significant difference."* — vague hedge, no explanation of why.
3. **Uncertain case:** *"...universities send letters like that to everyone to convince/trick people into applying who have no shot of getting in so they can improve their admissions statistics and look competitive. Those letters mean nothing."* — cynical and dismissive in tone, which first read as Gatekeeping-adjacent. But the hostility targets *colleges' marketing practices*, not the asker, and it gives a real, specific, informative claim (why the letters get sent). Decision: **Thorough**, not Discouraging or Gatekeeping. This case is why the decision rule says hostility must target the asker specifically — general cynicism about "the system" doesn't trigger Gatekeeping, and this comment actually clears the specificity bar.

### Generic
1. *":/ don't worry, you will be just fine."* — pure reassurance, no specifics.
2. *"Lol yea most people have crazy stats on here so dont let it get to you... were not all 'ivy league or suicide' types on here haha"* — reassurance plus a tangential personal aside, nothing applicable to the asker's actual profile.
3. **Uncertain case:** *"Then I see no reason why you wouldn't be accepted. That's a great gpa, and your extra curricular activities look great. Good luck, I think you have a good shot!"* — references the asker's actual profile (GPA, ECs), which feels more substantive than empty cheerleading. But it never states an actual number or makes a real comparison — "great gpa" isn't a data point. Decision: **Generic** — evaluative language about the asker's profile, without a concrete number/comparison/named outcome, doesn't clear the Thorough bar.

## Hard edge cases (summary)

The four uncertain cases above are the real recurring tensions; the single hardest anticipated edge case is **specific-but-hostile**: a reply that cites real numbers/named schools AND insults the asker in the same breath (the HMC/"you're delusional" example). Gut instinct wants to reward the specificity; the decision rule overrides that and calls it Gatekeeping, because a take that's technically correct but delivered as an attack isn't the kind of "good take" this taxonomy is trying to surface — tone of delivery toward the asker is the higher-priority signal. Second-hardest: **vague-but-not-empty** (the "great gpa... good shot!" example) — referencing the asker's real profile without a real number still doesn't clear the Thorough bar.

## Evaluation metrics

- **Overall accuracy** for both models, on the same held-out test set — baseline sanity check, but not sufficient alone.
- **Macro-F1** as the primary metric, not accuracy. The label distribution is expected to be uneven (Generic likely most common, Gatekeeping/Discouraging rarer), so a model that mostly predicts Generic could post a deceptively high accuracy while failing on the labels that actually matter for "what makes a good take" — macro-F1 weights all 4 classes equally regardless of frequency.
- **Per-class precision/recall**, especially recall on Gatekeeping and Thorough specifically: missing a Gatekeeping comment (false negative) is a worse failure for a discourse-quality tool than confusing Discouraging/Generic, since Gatekeeping is the label most useful to flag.
- **Confusion matrix** to check whether errors cluster along the two documented decision-rule boundaries (Gatekeeping↔Thorough on hostile-but-specific text; Generic↔Thorough on vague-profile-praise text) — if they do, that confirms the model is struggling with the same boundary a human annotator had to think hardest about, not failing randomly.

## Definition of success

- **Good enough to report as a working classifier:** fine-tuned macro-F1 ≥ 0.55 on the test set, and a clear, consistent improvement over the Groq zero-shot baseline's macro-F1 (fine-tuning should buy something — if it doesn't beat the baseline, that's a real finding to report honestly, not a target met).
- **Good enough for a real (non-deployed) community tool:** recall ≥ 0.6 on Gatekeeping specifically, since that's the label with the clearest "flag this for a human" use case, while precision on Thorough stays high enough (≥ 0.6) that the tool isn't burying genuinely good replies under false positives.
- **Not good enough for autonomous deployment regardless of metrics:** this is a 4-way subjective judgment call on a few hundred examples — explicitly scoped as a triage/flagging aid for human moderators, not an auto-moderation system, no matter what the numbers say. If test accuracy comes back above ~95%, that's a red flag for test-set leakage or labels that are too easy, not a win (per the project hints).

## AI Tool Plan

- **Label stress-testing:** before finalizing annotation, ask an LLM (Claude or Groq) to generate 5–10 synthetic A2C-style replies designed to sit at the Gatekeeping/Thorough and Generic/Thorough boundaries. If any come back genuinely unclassifiable under the current decision rule, tighten the rule before annotating further. Not yet run — planned as the last check before the full 200+ annotation pass.
- **Annotation assistance: revised decision, used pre-labeling with disclosure.** Originally planned to skip LLM pre-labeling entirely (see git history) to avoid two risks: (1) correlating the fine-tuned model's learned signal with whatever bias the labeler has, muddying the baseline-vs-finetune comparison; (2) shortcutting the hands-on annotation judgment that's the actual point of this milestone. After collecting 820 raw candidates and finding Gatekeeping/Discouraging genuinely rare even after 3 targeted mining passes, hand-reading all of them to pick a balanced final set became the bottleneck, so Claude (not Groq llama-3.3-70b-versatile, which is the baseline model being evaluated later — using it to pre-label would make that comparison circular) pre-labeled every candidate by applying the decision rule above. Every suggestion is shown in `scripts/annotate.py` next to the actual text and must be explicitly accepted (Enter) or overridden (typing a different label) — nothing is bulk-accepted. Final agreement rate between human label and Claude's suggestion is computed by comparing the `label` and `suggested_label` columns in `data/raw_candidates.csv`, and gets reported in the README as a transparency check on how much the human review actually changed.
- **Failure analysis:** after evaluation, give the full list of test-set misclassifications (both models) to an LLM and ask it to propose systematic patterns (e.g., "short replies misclassified as Generic," "sarcasm read as Thorough"). Each proposed pattern gets manually checked against the actual flagged examples before it goes in the eval report — an LLM-proposed pattern is a hypothesis to verify, not a finding to cite directly.

## Out of scope (excluded during annotation, not a label)
- Pure questions with no opinion/take content
- Jokes/anecdotes/dreams with no actual take ("I had a dream I got into Yale without even applying")
- Removed/[deleted]/AutoModerator/bot comments

## Data collection plan
- First pass: 420 raw candidates (`scripts/extract_candidates.py`), stratified across 4 keyword-heuristic buckets. Claude pre-labeled the pool against the decision rule (see AI Tool Plan below); real distribution came back ~77% Thorough among actual takes — Gatekeeping/Discouraging keyword hits almost always turned out to be Thorough once read in full, since this community backs up even blunt/negative takes with a number or named school.
- Second pass (`scripts/mine_rare_labels.py`): +200 candidates targeting hostile-toward-asker and vague-pessimism language specifically. Yielded 15 more Gatekeeping but only 4 more Discouraging.
- Third pass (`scripts/mine_discouraging.py`): +200 candidates requiring pessimism language AND the absence of any digit (digits correlate almost perfectly with Thorough in this corpus). Yielded a handful more genuine Discouraging examples.
- Final raw pool: 820 candidates, 281 SKIP (not opinions/takes), 539 real takes: Thorough 386 (72%), Generic 117 (22%), Gatekeeping 21 (4%), Discouraging 15 (3%).
- **Finding:** Gatekeeping and Discouraging are genuinely rare in r/ApplyingToCollege even under deliberate oversampling — this is a real property of the community's discourse, not a mining failure, and goes in the README reflection.
- Curated final pool (`scripts/curate_final_pool.py`): all 21 Gatekeeping + all 15 Discouraging kept, Thorough/Generic subsampled to 130/54 — 220 total, Thorough at 59% (under the 70% hard ceiling), Gatekeeping/Discouraging under the 20% aspiration but that's now a documented finding rather than an oversight. Full unfiltered 820-row pool archived at `data/raw_candidates_full_pool.csv` in case more rare-label examples are needed.

## Model/pipeline
- Base model: distilbert-base-uncased
- Fine-tuning: Colab starter notebook (T4 GPU)
- Baseline: Groq llama-3.3-70b-versatile, zero-shot prompt on same test set

## Stretch features
- Not yet decided — revisit after baseline results are in.
