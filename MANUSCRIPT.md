# MedCheck: Drug Interaction Chatbot

Nov 25, 2026 · @deniz

## Abstract

MedCheck is a chatbot that tells a user whether two medicines interact, how serious the interaction is, and what it does. The answer comes from a drug-interaction dataset and a model we trained on it, not from a general chatbot guessing. On 64,094 drug pairs it never saw in training, MedCheck detects interactions with 84.9% accuracy and classifies severity with 83.2% accuracy. Tuned for safety, it finds 92.6% of major interactions and calls only 2.5% of them "no interaction".

## Problem and why it matters

Many people take more than one medicine at once, often prescribed by different doctors or bought over the counter. Some combinations are harmful: they can cause bleeding, change how well a drug works, or add up side effects. Most people have no quick, reliable way to check a pair before taking it.

General chatbots can answer this question, but they can invent interactions or miss real ones, and they cannot show where an answer came from. For medicine, a confident wrong answer is dangerous.

## What we predict, and how early

For any pair of medicines, MedCheck predicts three things:

1. **Interaction or not:** whether the two drugs are known to interact.
2. **Severity:** minor, moderate or major.
3. **Effect:** what the interaction does, in plain language (for example, higher bleeding risk).

The warning comes before the person takes the second medicine: at home, at the pharmacy counter, or when a new prescription arrives. It does not replace a doctor or pharmacist; it tells the user when to ask one.

## Data and model

MedCheck has two parts: a model that finds the interaction, and a chatbot that talks to the user. The chatbot never decides the answer; it only explains what the model found.

**Data.** We use DDInter, which lists drug pairs with their interaction severity. After merging its 8 files and removing duplicates, we have 160,235 unique interacting pairs: 26,914 major, 96,675 moderate, 6,833 minor and 29,813 with no severity rating. We added non-interacting pairs so the model also learns what "safe" looks like.

**Model.** Two gradient-boosted tree classifiers (scikit-learn HistGradientBoostingClassifier): one predicts whether a pair interacts, the other predicts minor, moderate or major. Each drug is described by its known interactions (how many, and what share are minor, moderate or major), and each pair by how many interaction partners the two drugs share. Training features are built out-of-fold, so a pair's own label never leaks into its features. Instead of a 50% cut-off, we use safety thresholds picked on a separate 10% validation split: a pair counts as interacting above 18.6% probability, and as major above 25.5%. Pairs already in DDInter are answered directly from the data; the models only estimate pairs that are not listed. A name matcher maps brand names and typos (e.g. "Advil" to ibuprofen) to the right drug before the model runs.

**Chatbot.** \[Name the LLM.\] It reads the user's message, pulls out the drug names, and turns the model's output into a short, plain-language answer.

&#91;embedded content: MedCheck pipeline · 6 steps\]

The user only talks to the chatbot, but the interaction answer always comes from the model and its data.

## How we tested it

We split the interaction data into training and test sets (80/20) so the model is scored on drug pairs it never saw. We also built a hand-checked set of \[N\] well-known pairs to test the full chatbot end to end.

| Test | What it measures | Default (50% cut-off) | Safety thresholds |
| --- | --- | --- | --- |
| Interaction detection | Interaction vs. no interaction, 64,094 test pairs | 84.9% accuracy, 0.854 F1 | 78.1% accuracy, 0.816 F1 |
| Severity | Minor / moderate / major, 26,031 rated test pairs | 83.2% accuracy, 0.743 macro F1 | 77.8% accuracy, 0.707 macro F1 |
| Baseline | Always guessing "moderate" | 74.1% accuracy, about 0.28 macro F1 | same |
| Major recall | Major pairs rated major | 85.5% | 92.6% |
| Missed major interactions | Major pairs called "no interaction" (of 5,356) | 409 | 133 |
| Drug name matching | Brand names and typos mapped to the right drug | \[X\] of \[N\] |  |
| End-to-end chatbot | Known pairs (e.g. warfarin + aspirin) answered correctly | \[X\] of \[N\] |  |

Missed major interactions matter most: a false alarm costs a question to a pharmacist, a miss can cost harm. So MedCheck uses the safety thresholds: misses drop by 67%, at the cost of about 1,800 more moderate pairs flagged as major.

## Limits and next steps

**Limits**

- Not medical advice: MedCheck tells users when to ask a doctor or pharmacist, not what to do.
- It only knows drugs in the dataset; an unknown drug gets "not in our data", never a guess.
- It checks two drugs at a time, not a full medicine list.
  - "No interaction" training pairs are random pairs DDInter does not list, which is an approximation: a missing pair is not proof of safety.
  - 29,813 known interactions (19%) have no severity rating in DDInter; we report these as "interaction, severity unrated".
  - The model misses some dangerous pairs: even with safety thresholds, 2.5% of major test pairs were called "no interaction", and only 54% of major alarms are truly major.
- It ignores dose, age, kidney or liver function, and other conditions that change risk.

**Next steps**

- Check a whole medicine list, every pair at once.
- Add food and alcohol interactions (for example, grapefruit).
- Show the source record behind every answer.
- Support more languages, starting with \[Turkish\].

## Team and build log

| Name | Role | Builds | Writes | Presents |
| --- | --- | --- | --- | --- |
| Deniz | Data & Model | Dataset cleaning, interaction + severity model, model tests | Data and model; How we tested it | How it works; Results |
| Deniz | Chatbot & Interface | LLM connection, drug name extraction, plain-language answers, web interface | Chatbot part; Limits and next steps | Hook and problem; Live demo |
| Deniz | Name Matching, Integration & Testing | Name matcher, model-to-chatbot connection, hand-checked test list | Problem; What we predict; build log | Team and what's next; backup demo video |

Shared: agree on the model's input and output on day one, read the final manuscript together, and everyone tests the demo before the final day.

Add a line here every day you work: what you built, what you tried, what number you got. These notes become the results and limits sections above.

| Date | What we did | Result or decision |
| --- | --- | --- |
| \[date\] | \[e.g. picked dataset\] | \[e.g. DDInter, N pairs\] |
