"""
Train two models:
  1. Interaction model: does this pair interact? (yes / no)
  2. Severity model: Minor / Moderate / Major (pairs rated "Unknown" are left out)

Then pick safety thresholds on a 10% validation split (see decision.py).

Run from the project folder (after prepare_data.py):
    python -m model.train
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from model.decision import pick_thresholds
from model.features import DrugStats, build_matrix, build_oof_matrix

DATA_DIR = Path("data/processed")
MODEL_PATH = Path("models/medcheck.pkl")
SEVERITY_CLASSES = ["Minor", "Moderate", "Major"]
VALIDATION_SIZE = 0.1
SEED = 42


def main() -> None:
    data = pd.read_csv(DATA_DIR / "train.csv")
    is_val = np.random.default_rng(SEED).random(len(data)) < VALIDATION_SIZE
    train, val = data[~is_val].reset_index(drop=True), data[is_val].reset_index(drop=True)
    print(f"Training rows: {len(train):,}, validation rows: {len(val):,}")

    print("Building features...")
    X = build_oof_matrix(train)

    print("Training interaction model...")
    interaction_model = HistGradientBoostingClassifier(max_iter=300, random_state=SEED)
    interaction_model.fit(X, train["interaction"])

    print("Training severity model...")
    rated = train["Level"].isin(SEVERITY_CLASSES).to_numpy()
    severity_model = HistGradientBoostingClassifier(
        max_iter=300, class_weight="balanced", random_state=SEED
    )
    severity_model.fit(X[rated], train.loc[rated, "Level"])

    art = {"interaction_model": interaction_model, "severity_model": severity_model}

    print("Picking safety thresholds on the validation set...")
    train_stats = DrugStats(train[train["interaction"] == 1])
    X_val = build_matrix(val, train_stats)
    art["thresholds"] = pick_thresholds(art, X_val, val["Level"].to_numpy())
    print(f"  interaction threshold: {art['thresholds']['interaction_threshold']:.3f}")
    print(f"  major threshold:       {art['thresholds']['major_threshold']:.3f}")

    # Statistics from ALL training data, used for test pairs and new pairs.
    art["stats"] = DrugStats(data[data["interaction"] == 1])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(art, MODEL_PATH)
    print(f"Saved models to {MODEL_PATH}")


if __name__ == "__main__":
    main()
