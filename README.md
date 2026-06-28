# TakeMeter — Discourse-Quality Classifier for r/ApplyingToCollege

A fine-tuned 4-way text classifier that labels the *quality* of replies in r/ApplyingToCollege (A2C) "chance me" / admissions-strategy threads. It distinguishes hostile gatekeeping, substantive feedback, empty pessimism, and generic cheerleading — the same distinctions A2C regulars already make when they decide which replies are worth reading.

Full design notes, decision rules, and data-collection log live in [planning.md](planning.md). This README is the standalone report.

---

## 1. Community & why it fits

**Community:** [r/ApplyingToCollege](https://www.reddit.com/r/ApplyingToCollege/) — college applicants and admitted students. Recurring thread types: "chance me" admissions assessments, school-choice debates, stats (GPA/SAT/ACT) comparisons, and application-strategy questions.

**Why it's a good classification target:** A2C is high-volume and high-stakes. Every "chance me" thread mixes genuinely useful, specific feedback with empty cheerleading and outright elitist dismissal — and regulars actively complain about both ("this sub is just gatekeeping" / "stop with the generic good-luck spam"). The discourse-quality distinction is real, contested, and recognizable to participants, which is exactly what makes it a meaningful (and hard) label task rather than a trivial topic-classification one.

*(Originally scoped to r/MBA; pivoted to A2C because Reddit's current Data API terms prohibit live scraping for ML training, and a static non-commercial research corpus exists for A2C. Same discourse pattern, vocabulary swap GMAT/M7 → SAT/T20. Full rationale in [planning.md](planning.md).)*

---

## 2. Label taxonomy

Two axes — **substance** (specific vs. vague) and **tone** (hostile vs. not) — collapsed into one decision rule, checked top-to-bottom, first match wins, so every post gets exactly one label.

| Label | Definition | Example 1 | Example 2 |
|---|---|---|---|
| **gatekeeping** | Dismissive, mocking, or elitist; attacks the *asker's* legitimacy/credentials directly. Hostility toward the asker wins even if specifics are present. | *"No, honestly, that's pathetic. I'll have the Ivy League brand to back me up when I graduate."* | *"Just make sure you're not ugly af. And if you are, get real good at photoshop in the next few hours."* |
| **thorough** | Not hostile, backed by specific reasoning — numbers, named schools/outcomes, real tradeoffs, or genuinely informative explanation. Conclusion may be positive **or** negative. | *"I got into DGS with a 1370 SAT… DGS is the easiest major to get admitted into. My GPA was a 3.18 UW."* | *"700 on math is 66th percentile. If your school requires subject tests, send it."* |
| **discouraging** | Not hostile, not specific, pessimistic with no real reasoning given. | *"Probably won't get paid though."* (re: journalism internships) | *"It's a pretty good thing to put on your resume but don't count on it making a significant difference."* |
| **generic** | Everything else — platitudes, cheerleading, vague evaluative language ("great GPA," "looks good") with no concrete number/comparison/named outcome. | *":/ don't worry, you will be just fine."* | *"Lol yea most people have crazy stats on here so dont let it get to you."* |

**Decision rule (check order):** hostile toward the *asker*? → gatekeeping. Else specific? → thorough. Else pessimistic? → discouraging. Else → generic.

---

## 3. Data

**Source:** [ConvoKit Reddit Corpus — r/ApplyingToCollege](https://convokit.cornell.edu/documentation/subreddit.html) (Cornell Social Dynamics Lab, 2019 Pushshift snapshot, distributed for non-commercial NLP research). Downloaded the corpus archive directly — **not** via Reddit's live API — to stay within current ToS. Corpus: 121K posts, 1.0M comments.

**Labeling process:**
1. `scripts/extract_candidates.py` streamed the corpus, kept top-level comments and substantial posts, filtered `[deleted]`/`[removed]`/AutoModerator/stubs, and stratified sampling by a keyword heuristic so the pool wasn't ~90% generic. *The heuristic is sampling scaffolding only — never the label.*
2. Three mining passes (`mine_rare_labels.py`, `mine_discouraging.py`) oversampled hostile/pessimistic language to chase the rare classes → 820 raw candidates.
3. Every candidate was **pre-labeled by Claude** against the decision rule, then reviewed one-by-one in `scripts/annotate.py` (each suggestion shown next to the post text; accept or override per row). See [§9 AI usage](#9-ai-usage) for the disclosure and agreement caveat.
4. `scripts/curate_final_pool.py` kept **all** rare-class examples and subsampled the common ones to the final 220.

**Final label distribution (220 examples):**

| Label | Count | Share |
|---|---|---|
| thorough | 130 | 59% |
| generic | 54 | 25% |
| gatekeeping | 21 | 10% |
| discouraging | 15 | 7% |

No label exceeds the 70% imbalance ceiling, **but** gatekeeping and discouraging fall well under the 20% aspiration. This is a **real property of the community** — even after three deliberate oversampling passes, hostile and content-free-pessimistic replies are genuinely rare in A2C, because the sub backs up even blunt/negative takes with a number or named school. This rarity is the single biggest driver of the model's behavior (see §6).

**3 genuinely difficult examples and how they were decided:**

1. **Specific *and* hostile** — *"…Even HMC's average is below that. There is no need to worry… If you think 70 points will make that big of a deal, you're delusional."* Has real specifics (named school, score comparison) **and** a direct insult. → **gatekeeping.** Hostility toward the asker outranks specificity in the check order; a correct take delivered as an attack isn't the "good take" this taxonomy surfaces.
2. **Cynical but not toward the asker** — *"…universities send letters like that to trick people into applying who have no shot… Those letters mean nothing."* Reads gatekeeping-adjacent, but the hostility targets *colleges' marketing*, not the asker, and it makes a real informative claim. → **thorough.** This case is *why* the rule requires hostility to target the asker specifically.
3. **Vague but not empty** — *"That's a great gpa, and your extra curricular activities look great. Good luck, I think you have a good shot!"* References the asker's actual profile, which feels more substantive than pure cheerleading — but it states no number or real comparison. → **generic.** "Great gpa" is not a data point.

---

## 4. Fine-tuning approach

- **Base model:** `distilbert-base-uncased` (HuggingFace) with a freshly-initialized 4-class classification head.
- **Setup:** Google Colab T4 GPU. Stratified 70/15/15 split → **154 train / 33 val / 33 test**. Max sequence length 256, `DataCollatorWithPadding`.
- **Hyperparameters:** 3 epochs, learning rate 2e-5, batch size 16, weight decay 0.01, 50 warmup steps. Best checkpoint by validation accuracy.

**Key hyperparameter decision — kept the default loss (unweighted) and 3 epochs.** With only 154 training rows (91 of them `thorough`), I deliberately did *not* add class weighting or extra epochs on this run, to first see what the vanilla pipeline learns. The result (§6) is that the model collapsed to predicting the majority class. That is reported here honestly as the finding rather than hidden — the documented next step is inverse-frequency class weighting and 5 epochs to force the model off the prior.

---

## 5. Baseline

**Zero-shot Groq `llama-3.3-70b-versatile`**, no task-specific training, evaluated on the **same 33-example test set**. The prompt names the community, defines all four labels in plain language with one example each, and instructs the model to output only the lowercase label name (parsed by exact/substring match against the label set). Full prompt is in the notebook (Section 5).

Using Groq for the baseline (and **Claude**, a *different* model, for annotation pre-labeling) keeps the baseline-vs-fine-tune comparison independent — the baseline model never touched the training labels.

---

## 6. Evaluation report

### Overall accuracy

| Model | Accuracy |
|---|---|
| Zero-shot baseline (Groq llama-3.3-70b) | **0.515** |
| Fine-tuned DistilBERT | **0.606** |
| **Fine-tuning improvement** | **+0.091** |

Fine-tuning beat the baseline on raw accuracy — but accuracy is misleading here, because 0.606 is *exactly* the `thorough` base rate in the test set (20/33). See per-class metrics.

### Per-class metrics — Fine-tuned DistilBERT

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| gatekeeping | 0.00 | 0.00 | 0.00 | 3 |
| thorough | 0.61 | 1.00 | 0.76 | 20 |
| discouraging | 0.00 | 0.00 | 0.00 | 2 |
| generic | 0.00 | 0.00 | 0.00 | 8 |
| **macro avg** | **0.15** | **0.25** | **0.19** | 33 |
| weighted avg | 0.37 | 0.61 | 0.46 | 33 |

**Macro-F1 = 0.19**, far below the 0.55 success bar set in [planning.md](planning.md). The headline accuracy of 0.606 is entirely an artifact of class imbalance.

### Per-class metrics — Baseline (Groq)

<!-- TODO: paste the Section 5 baseline `classification_report` output here.
     Need per-class precision/recall/F1 for the four labels to complete this table. -->

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| gatekeeping | _paste_ | _paste_ | _paste_ | 3 |
| thorough | _paste_ | _paste_ | _paste_ | 20 |
| discouraging | _paste_ | _paste_ | _paste_ | 2 |
| generic | _paste_ | _paste_ | _paste_ | 8 |

*(Baseline overall accuracy 0.515 confirmed; per-class table pending the Section 5 report paste.)*

### Confusion matrix — Fine-tuned DistilBERT (test set)

Rows = true label, columns = predicted label.

| true ↓ / pred → | gatekeeping | thorough | discouraging | generic |
|---|---|---|---|---|
| **gatekeeping** | 0 | 3 | 0 | 0 |
| **thorough** | 0 | **20** | 0 | 0 |
| **discouraging** | 0 | 2 | 0 | 0 |
| **generic** | 0 | 8 | 0 | 0 |

(Image: [confusion_matrix.png](confusion_matrix.png).)

**The matrix is one column.** The model predicts `thorough` for all 33 test examples and never emits the other three labels. This is textbook majority-class collapse: with 59% of training data labeled `thorough` and only 10/154 `discouraging` and 15/154 `gatekeeping` rows, the cheapest thing for an unweighted loss to learn is the prior.

### 3 specific wrong predictions + analysis

All errors share one direction — `X → thorough` — so they're best read as three faces of the same collapse, not three independent mistakes.

1. **True `gatekeeping` → predicted `thorough`:** *"Are you dumb, Cornell is one of the best engineering schools in the world."* The post names a school (a feature strongly correlated with `thorough` in training) while its actual signal — the insult "Are you dumb" — lives on the *tone* axis the model never learned, because 15 training examples aren't enough to carve out the hostility boundary. The surface token "Cornell" wins.
2. **True `discouraging` → predicted `thorough`:** *"Probably won't get paid though."* Ten `discouraging` training rows gave the model no learnable signal for flat, content-free pessimism, so it defaults to the prior. A correct classifier would need far more examples of short pessimistic replies.
3. **True `generic` → predicted `thorough`:** *"If you don't tell any college, they probably wont know."* Vague, no number, no named outcome — should be `generic`. The model has no discriminative boundary at all, so even the second-largest class (generic, 8 test rows) is absorbed into `thorough`.

**Is this a labeling problem or a data problem?** A data problem. The hard edge cases were labeled consistently per the decision rule (§3), and the model still gets them wrong *uniformly* — it isn't confusing specific boundaries, it's ignoring three of four classes entirely. The fix is class rebalancing (inverse-frequency weighted loss, oversampling the rare classes, or collecting more gatekeeping/discouraging examples), not relabeling.

### Sample classifications

Posts run through the fine-tuned model with predicted label + confidence (softmax of the predicted class).

<!-- TODO: paste confidence values from the Section 4 "wrong predictions" cell (8b426824)
     and/or run a few posts through the model. Predicted label is `thorough` for all
     (model collapse), so only the confidence column needs filling. -->

| # | Post (truncated) | True label | Predicted | Confidence |
|---|---|---|---|---|
| 1 | *"700 on math is 66th percentile. If your school requires subject tests, send it."* | thorough | thorough | _paste_ |
| 2 | *"Are you dumb, Cornell is one of the best engineering schools in the world."* | gatekeeping | thorough | _paste_ |
| 3 | *"Probably won't get paid though."* | discouraging | thorough | _paste_ |
| 4 | *"If you don't tell any college, they probably wont know."* | generic | thorough | _paste_ |

**Why #1 is a reasonable prediction:** it cites a concrete number (66th percentile) and gives conditional, actionable reasoning — a clean `thorough` post, and the one class the model actually learned. Its correctness is real signal, unlike #2–4 which are correct-label-by-accident only when the true label happens to be `thorough`.

---

## 7. Reflection — what the model learned vs. what I intended

I intended a 4-way *discourse-quality* classifier that captures two independent signals: **substance** (is there a number/named outcome/real reasoning?) and **tone** (is this hostile to the asker?). What the model actually learned was **the marginal distribution of the labels** — "say thorough" — and nothing about either axis.

The gap is instructive. My taxonomy treats tone as a first-class, highest-priority signal (gatekeeping overrides everything). But tone is exactly the axis with the fewest examples, so the model had no way to learn it; it overfit to the single dominant class and to surface lexical cues (school names, digits) that correlate with `thorough`. The intended decision *boundary* — "hostile-but-specific → gatekeeping, not thorough" — requires the model to weigh tone over substance, and it learned the opposite default (substance cues → thorough) because that's what the data frequency rewards.

The deeper lesson: the rarity of gatekeeping/discouraging isn't noise to be engineered away — it's a true feature of A2C discourse. A faithful classifier has to be *built around* that imbalance (weighted loss, targeted collection, or reframing as flag-the-rare-class detection), not trained as if the four classes were balanced.

---

## 8. Spec reflection

**One way the spec helped:** the planning doc forced an explicit, ordered decision rule *before* annotation. When I hit the "specific-but-hostile" example mid-labeling, I didn't have to improvise — the rule already said hostility-toward-asker wins, and I labeled consistently. That consistency is exactly why §6 can confidently call the failure a data problem, not a labeling one.

**One way the implementation diverged:** the spec set macro-F1 ≥ 0.55 as the success bar and assumed fine-tuning would beat the baseline meaningfully. The implementation diverged hard — the model collapsed to the majority class (macro-F1 0.19) and only "beat" the baseline on an accuracy number that's an imbalance artifact. Rather than chase the threshold by quietly rerunning with tricks, I'm reporting the collapse as the honest finding, which the spec's own "if it doesn't beat the baseline, that's a real finding to report" clause explicitly anticipated.

---

## 9. AI usage

1. **Annotation pre-labeling (disclosed).** Claude pre-labeled all 820 raw candidates against the decision rule. I reviewed every candidate in `scripts/annotate.py`, which shows each suggestion next to the post text and requires an explicit keypress per row (accept = Enter, override = type a different label). **Agreement caveat:** under time pressure I accepted the suggestions on the final 220-row pass rather than overriding any, so the human-vs-suggestion agreement rate is effectively 100% — meaning this run is *not* an independent check on Claude's labels. The decision rule and the hard-case decisions (§3) are my own, written before pre-labeling. Groq's `llama-3.3-70b` (the evaluated baseline) was deliberately **not** used for pre-labeling, to keep the baseline comparison non-circular.
2. **Label stress-testing & build assistance.** I used Claude to derive the fine-tuning notebook's required edits (label map, lowercase normalization, Groq prompt) and to reproduce the exact stratified test split locally for error analysis. I verified each edit against the notebook before running, and confirmed the reproduced split sizes matched the notebook's reported splits.
3. **Failure-pattern analysis.** I gave the list of test-set misclassifications to Claude to surface patterns; it identified the uniform `X → thorough` collapse, which I then verified directly against the confusion matrix (§6) before writing it up.

---

## Repo contents

- [planning.md](planning.md) — full design doc (labels, decision rule, data log, AI tool plan)
- [data/labeled_dataset.csv](data/labeled_dataset.csv) — 220 labeled examples (`text`, `label`, `notes`)
- [data/raw_candidates.csv](data/raw_candidates.csv) — working annotation file (extra columns + suggestions)
- `scripts/` — extraction, mining, annotation, export pipeline
- [evaluation_results.json](evaluation_results.json) — metrics export from Colab
- [confusion_matrix.png](confusion_matrix.png) — fine-tuned confusion matrix
- `*.ipynb` — Colab fine-tuning + baseline notebook
