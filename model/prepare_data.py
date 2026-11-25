"""
Combine the DDInter CSV files, clean them, add "no interaction" pairs,
and split into train/test sets.

Input:  data/raw/ddinter_downloads_code_*.csv
Output: data/processed/interactions.csv  (all known interactions, cleaned)
        data/processed/train.csv
        data/processed/test.csv

Run from the project folder:
    python model/prepare_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
SEED = 42
TEST_SIZE = 0.2
NEGATIVES_PER_POSITIVE = 1.0  # how many "no interaction" pairs per real one

# Higher number = more severe. Used to keep the worst level if a pair repeats.
SEVERITY_RANK = {"Unknown": 0, "Minor": 1, "Moderate": 2, "Major": 3}


def load_raw() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("ddinter_downloads_code_*.csv"))
    if not files:
        raise FileNotFoundError(f"No DDInter CSV files found in {RAW_DIR}/")
    print(f"Found {len(files)} files")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    print(f"Rows before cleaning: {len(df):,}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["DDInterID_A", "DDInterID_B", "Level"]).copy()
    for col in ["DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B", "Level"]:
        df[col] = df[col].astype(str).str.strip()

    # A+B and B+A are the same pair: always put the smaller ID first.
    swap = df["DDInterID_A"] > df["DDInterID_B"]
    df.loc[swap, ["DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B"]] = df.loc[
        swap, ["DDInterID_B", "Drug_B", "DDInterID_A", "Drug_A"]
    ].values

    # Drop a drug paired with itself.
    df = df[df["DDInterID_A"] != df["DDInterID_B"]]

    # The same pair can appear in several files: keep the most severe level.
    df["rank"] = df["Level"].map(SEVERITY_RANK).fillna(0)
    df = (
        df.sort_values("rank", ascending=False)
        .drop_duplicates(subset=["DDInterID_A", "DDInterID_B"])
        .drop(columns="rank")
    )

    df["interaction"] = 1
    print(f"Unique interacting pairs: {len(df):,}")
    print("Severity counts:")
    print(df["Level"].value_counts().to_string())
    return df.reset_index(drop=True)


def make_negatives(pos: pd.DataFrame) -> pd.DataFrame:
    """Random drug pairs that never appear together in DDInter.

    These are *assumed* safe. DDInter not listing a pair does not prove there
    is no interaction, so this is an approximation (mention it in Limits).
    """
    rng = np.random.default_rng(SEED)
    names = dict(zip(pos["DDInterID_A"], pos["Drug_A"]))
    names.update(zip(pos["DDInterID_B"], pos["Drug_B"]))
    ids = np.array(sorted(names))
    known = set(zip(pos["DDInterID_A"], pos["DDInterID_B"]))

    target = int(len(pos) * NEGATIVES_PER_POSITIVE)
    found = set()
    while len(found) < target:
        a, b = rng.choice(ids, size=2, replace=False)
        a, b = min(a, b), max(a, b)
        if (a, b) not in known:
            found.add((a, b))

    neg = pd.DataFrame(sorted(found), columns=["DDInterID_A", "DDInterID_B"])
    neg["Drug_A"] = neg["DDInterID_A"].map(names)
    neg["Drug_B"] = neg["DDInterID_B"].map(names)
    neg["Level"] = "None"
    neg["interaction"] = 0
    print(f"Generated 'no interaction' pairs: {len(neg):,}")
    return neg[pos.columns]


def split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Each row is a unique pair, so a shuffled row split never puts the
    # same pair in both train and test.
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    n_test = int(len(df) * TEST_SIZE)
    return df.iloc[n_test:], df.iloc[:n_test]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pos = clean(load_raw())
    pos.to_csv(OUT_DIR / "interactions.csv", index=False)

    data = pd.concat([pos, make_negatives(pos)], ignore_index=True)
    train, test = split(data)
    train.to_csv(OUT_DIR / "train.csv", index=False)
    test.to_csv(OUT_DIR / "test.csv", index=False)
    print(f"Train: {len(train):,} rows, Test: {len(test):,} rows")
    print(f"Saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()