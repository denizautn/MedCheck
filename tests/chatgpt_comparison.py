"""
Compare MedCheck with ChatGPT on 30 random drug pairs.

Step 1: pick the pairs (fixed random seed, so anyone can repeat it)
    python -m tests.chatgpt_comparison

    Writes results/chatgpt_comparison.csv and prints a question for each pair.
    Ask ChatGPT each question in a NEW chat, twice (the second time with the
    rephrased question), and type its answers into the columns
    chatgpt_answer_1 and chatgpt_answer_2 (none / minor / moderate / major).

Step 2: score it
    python -m tests.chatgpt_comparison --score

The pairs come from the test set: 10 major, 5 moderate, 5 minor from DDInter,
and 10 pairs listed in neither DDInter nor DrugBank. "Not listed" is not proof
that a pair is safe, so disagreements on those are reported separately.
"""

import sys
from pathlib import Path

import pandas as pd

from model.predict import predict

TEST_PATH = Path("data/processed/test.csv")
EFFECTS_PATH = Path("data/processed/effects.csv")
OUT_PATH = Path("results/chatgpt_comparison.csv")
SEED = 7
PLAN = {"Major": 10, "Moderate": 5, "Minor": 5, "None": 10}

QUESTION_1 = (
    "Do {a} and {b} interact? Answer with one word: none, minor, moderate or major."
)
QUESTION_2 = (
    "I take {b} and my doctor added {a}. How serious is the interaction between "
    "them? Reply with only one word: none, minor, moderate, or major."
)


def medcheck_answer(a: str, b: str) -> str:
    r = predict(a, b)
    if r.get("status") != "ok":
        return "not in data"
    if r["source"] == "DDInter":
        return r["severity"].lower()
    if not r["interaction"]:
        return "none"
    return r["estimated_severity"].lower() + " (estimate)"


def pick() -> None:
    test = pd.read_csv(TEST_PATH)
    # pandas reads the word "None" as empty, so use the interaction column instead.
    test.loc[test["interaction"] == 0, "Level"] = "None"
    if EFFECTS_PATH.exists():
        ef = pd.read_csv(EFFECTS_PATH)
        in_drugbank = set(zip(ef["DDInterID_A"], ef["DDInterID_B"]))
        not_db = [
            (a, b) not in in_drugbank for a, b in zip(test["DDInterID_A"], test["DDInterID_B"])
        ]
        test = test[(test["Level"] != "None") | pd.Series(not_db, index=test.index)]

    parts = [
        test[test["Level"] == level].sample(
            min(n, int((test["Level"] == level).sum())), random_state=SEED
        )
        for level, n in PLAN.items()
    ]
    pairs = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)

    rows = []
    for i, (a, b, level) in enumerate(zip(pairs["Drug_A"], pairs["Drug_B"], pairs["Level"]), 1):
        rows.append({
            "pair": i,
            "drug_a": a,
            "drug_b": b,
            "ddinter": "not listed" if level == "None" else level.lower(),
            "medcheck": medcheck_answer(a, b),
            "question_1": QUESTION_1.format(a=a, b=b),
            "question_2": QUESTION_2.format(a=a, b=b),
            "chatgpt_answer_1": "",
            "chatgpt_answer_2": "",
        })
    out = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    for r in rows:
        print(f"\n#{r['pair']:>2}  {r['drug_a']} + {r['drug_b']}   (DDInter: {r['ddinter']})")
        print(f"     Q1: {r['question_1']}")
        print(f"     Q2: {r['question_2']}")
    print(f"\nSaved to {OUT_PATH}. Fill in chatgpt_answer_1 and chatgpt_answer_2, then run:")
    print("    python -m tests.chatgpt_comparison --score")


def norm(x) -> str:
    return str(x).strip().lower().rstrip(".")


def score() -> None:
    df = pd.read_csv(OUT_PATH).fillna("")
    if (df["chatgpt_answer_1"] == "").all():
        print("Fill in chatgpt_answer_1 first.")
        return
    listed = df["ddinter"] != "not listed"
    c1, c2 = df["chatgpt_answer_1"].map(norm), df["chatgpt_answer_2"].map(norm)
    truth = df["ddinter"].map(norm)

    print(f"Pairs: {len(df)} ({listed.sum()} listed in DDInter, {(~listed).sum()} not listed)\n")
    print("Pairs listed in DDInter:")
    print(f"  ChatGPT severity matches DDInter: {(c1[listed] == truth[listed]).sum()} of {listed.sum()}")
    missed = listed & (c1 == "none")
    print(f"  ChatGPT said 'none' for a listed interaction: {missed.sum()}")
    major = truth == "major"
    print(f"  Major pairs ChatGPT called major: {(c1[major] == 'major').sum()} of {major.sum()}")
    print("\nPairs not listed in DDInter or DrugBank:")
    print(f"  ChatGPT reported an interaction: {((~listed) & (c1 != 'none')).sum()} of {(~listed).sum()}")
    if (c2 != "").any():
        both = c2 != ""
        print(f"\nConsistency: ChatGPT gave the same answer to both phrasings in "
              f"{(c1[both] == c2[both]).sum()} of {both.sum()} pairs")
    print("\nMedCheck answers listed pairs straight from DDInter, so it matches them by design.")
    print("Disagreeing with DDInter does not always mean ChatGPT is wrong: sources can differ.")


if __name__ == "__main__":
    score() if "--score" in sys.argv else pick()
