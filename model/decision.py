"""
Safety thresholds: how the models' probabilities become answers.

In medicine, missing a dangerous interaction is worse than a false alarm.
So instead of the default 50% cut-off, we pick thresholds (on a validation
set, never the test set) that catch most major interactions:

  - Interaction: say "interaction" if P(interaction) >= interaction_threshold
  - Severity:    say "Major" if P(Major) >= major_threshold,
                 otherwise the more likely of Minor / Moderate
"""

import numpy as np

TARGET_MAJOR_RECALL_INTERACTION = 0.97  # flag 97% of major pairs as interacting
TARGET_MAJOR_RECALL_SEVERITY = 0.92     # rate 92% of major pairs as Major
# Never go below these, so the model can't end up flagging everything.
MIN_INTERACTION_THRESHOLD = 0.10
MIN_MAJOR_THRESHOLD = 0.15


def pick_thresholds(art: dict, X_val: np.ndarray, levels_val: np.ndarray) -> dict:
    major = levels_val == "Major"

    p_inter = art["interaction_model"].predict_proba(X_val[major])[:, 1]
    interaction_threshold = float(np.clip(
        np.quantile(p_inter, 1 - TARGET_MAJOR_RECALL_INTERACTION),
        MIN_INTERACTION_THRESHOLD, 0.5,
    ))

    sev = art["severity_model"]
    major_col = list(sev.classes_).index("Major")
    p_major = sev.predict_proba(X_val[major])[:, major_col]
    major_threshold = float(np.clip(
        np.quantile(p_major, 1 - TARGET_MAJOR_RECALL_SEVERITY),
        MIN_MAJOR_THRESHOLD, 0.5,
    ))
    return {
        "interaction_threshold": interaction_threshold,
        "major_threshold": major_threshold,
    }


def interaction_proba(art: dict, X: np.ndarray) -> np.ndarray:
    return art["interaction_model"].predict_proba(X)[:, 1]


def predict_interaction(art: dict, X: np.ndarray, safe: bool = True) -> np.ndarray:
    threshold = art["thresholds"]["interaction_threshold"] if safe else 0.5
    return (interaction_proba(art, X) >= threshold).astype(int)


def predict_severity(art: dict, X: np.ndarray, safe: bool = True) -> np.ndarray:
    sev = art["severity_model"]
    if not safe:
        return sev.predict(X)
    classes = list(sev.classes_)
    proba = sev.predict_proba(X)
    major_col = classes.index("Major")
    others = [i for i, c in enumerate(classes) if c != "Major"]
    best_other = np.array(classes)[others][proba[:, others].argmax(axis=1)]
    is_major = proba[:, major_col] >= art["thresholds"]["major_threshold"]
    return np.where(is_major, "Major", best_other)
