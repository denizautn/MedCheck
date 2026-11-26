"""
Score both models on the test set (drug pairs the models never saw),
with the default 50% cut-off and with the safety thresholds.

Run from the project folder (after train.py):
    python -m model.evaluate

Prints the results and saves them to results/metrics.txt for the manuscript.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from model.decision import predict_interaction, predict_severity
from model.features import build_matrix

DATA_DIR = Path("data/processed")
MODEL_PATH = Path("models/medcheck.pkl")
RESULTS_PATH = Path("results/metrics.txt")
SEVERITY_CLASSES = ["Minor", "Moderate", "Major"]


def main() -> None:
    art = joblib.load(MODEL_PATH)
    test = pd.read_csv(DATA_DIR / "test.csv")
    X = build_matrix(test, art["stats"])
    lines = []

    def out(text=""):
        print(text)
        lines.append(text)

    y_true = test["interaction"].to_numpy()
    rated = test["Level"].isin(SEVERITY_CLASSES).to_numpy()
    s_true = test.loc[rated, "Level"].to_numpy()
    major = (test["Level"] == "Major").to_numpy()
    baseline = accuracy_score(s_true, np.full(len(s_true), "Moderate"))

    t = art["thresholds"]
    out(f"Test pairs: {len(test):,} (rated for severity: {rated.sum():,}, major: {major.sum():,})")
    out(f"Safety thresholds: interaction {t['interaction_threshold']:.3f}, "
        f"major {t['major_threshold']:.3f}")
    out()

    for safe, title in ((False, "DEFAULT (50% cut-off)"), (True, "SAFETY THRESHOLDS")):
        y_pred = predict_interaction(art, X, safe)
        s_pred = predict_severity(art, X[rated], safe)
        sev_major = predict_severity(art, X[major], safe)
        called_safe = int((y_pred[major] == 0).sum())
        not_flagged = int(((y_pred[major] == 0) | (sev_major != "Major")).sum())

        out(f"################ {title} ################")
        out("=== Interaction detection ===")
        out(f"Accuracy: {accuracy_score(y_true, y_pred):.3f}")
        out(f"F1:       {f1_score(y_true, y_pred):.3f}")
        out()
        out("=== Severity (Minor / Moderate / Major) ===")
        out(f"Accuracy:          {accuracy_score(s_true, s_pred):.3f}")
        out(f"Macro F1:          {f1_score(s_true, s_pred, average='macro'):.3f}")
        out(f"Baseline accuracy: {baseline:.3f}  (always guessing 'Moderate')")
        out()
        out(classification_report(s_true, s_pred, labels=SEVERITY_CLASSES, digits=3))
        out("Confusion matrix (rows = true, columns = predicted):")
        out(f"{'':>10}" + "".join(f"{c:>10}" for c in SEVERITY_CLASSES))
        cm = confusion_matrix(s_true, s_pred, labels=SEVERITY_CLASSES)
        for name, row in zip(SEVERITY_CLASSES, cm):
            out(f"{name:>10}" + "".join(f"{v:>10}" for v in row))
        out()
        out("=== Missed major interactions ===")
        out(f"Called 'no interaction':            {called_safe:,} of {major.sum():,}")
        out(f"Not flagged as Major (any reason):  {not_flagged:,} of {major.sum():,}")
        out()

    out("Note: in the app, pairs already listed in DDInter are looked up directly.")
    out("These scores measure how well the model predicts pairs NOT in the data.")

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
