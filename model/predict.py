"""
predict(drug_a, drug_b) -> dict

1. Match both names to drugs in DDInter (brand names and typos allowed).
2. If the pair is listed in DDInter, answer from the data.
3. If not, ask the model for an estimate (clearly marked as a prediction),
   using the safety thresholds from decision.py.

Try it from the project folder:
    python -m model.predict warfarin aspirin
"""

import sys
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from chatbot.name_matcher import NameMatcher
from model.decision import interaction_proba, predict_severity

MODEL_PATH = Path("models/medcheck.pkl")
INTERACTIONS_PATH = Path("data/processed/interactions.csv")
EFFECTS_PATH = Path("data/processed/effects.csv")  # optional, from prepare_effects.py


@lru_cache(maxsize=1)
def load():
    art = joblib.load(MODEL_PATH)
    df = pd.read_csv(INTERACTIONS_PATH)
    lookup = {
        (a, b): level
        for a, b, level in zip(df["DDInterID_A"], df["DDInterID_B"], df["Level"])
    }
    names = dict(zip(df["DDInterID_A"], df["Drug_A"]))
    names.update(zip(df["DDInterID_B"], df["Drug_B"]))
    return art, lookup, NameMatcher(names)


@lru_cache(maxsize=1)
def load_effects() -> dict:
    if not EFFECTS_PATH.exists():
        return {}
    ef = pd.read_csv(EFFECTS_PATH)
    return {
        (a, b): e.split("; ")
        for a, b, e in zip(ef["DDInterID_A"], ef["DDInterID_B"], ef["effects"])
    }


def get_matcher() -> NameMatcher:
    return load()[2]


def predict(drug_a: str, drug_b: str) -> dict:
    result = _predict(drug_a, drug_b)
    if result["status"] == "ok":
        effects = load_effects().get(result.pop("_ids"))
        if effects:
            result["effects"] = effects
            result["effects_source"] = "DrugBank"
            # Not in DDInter but listed in DrugBank: a second source confirms it.
            if result["source"] == "model":
                result["interaction"] = True
                result["source"] = "DrugBank"
                if "estimated_severity" not in result:
                    art = load()[0]
                    X = np.array([art["stats"].pair_features(*result["_pair"])])
                    result["estimated_severity"] = str(predict_severity(art, X)[0])
        result.pop("_ids", None)
        result.pop("_pair", None)
    return result


def _predict(drug_a: str, drug_b: str) -> dict:
    art, lookup, matcher = load()
    a, b = matcher.match(drug_a), matcher.match(drug_b)

    unknown = [name for name, m in ((drug_a, a), (drug_b, b)) if m is None]
    if unknown:
        return {"status": "unknown_drug", "unknown": unknown}
    if a[0] == b[0]:
        return {"status": "same_drug", "drug_a": a[1], "drug_b": b[1]}

    (id_a, name_a), (id_b, name_b) = sorted([a, b])
    result = {
        "status": "ok", "drug_a": name_a, "drug_b": name_b,
        "_ids": (id_a, id_b), "_pair": (id_a, id_b),
    }
    X = np.array([art["stats"].pair_features(id_a, id_b)])
    level = lookup.get((id_a, id_b))

    # 1. Known pair: answer straight from DDInter.
    if level is not None:
        result.update(interaction=True, source="DDInter")
        if level == "Unknown":
            result["severity"] = "Unrated"
            result["estimated_severity"] = str(predict_severity(art, X)[0])
        else:
            result["severity"] = level
        return result

    # 2. Not in DDInter: model estimate with safety thresholds.
    probability = float(interaction_proba(art, X)[0])
    threshold = art["thresholds"]["interaction_threshold"]
    result.update(
        source="model",
        interaction=probability >= threshold,
        probability=round(probability, 2),
        threshold=round(threshold, 2),
    )
    if result["interaction"]:
        result["estimated_severity"] = str(predict_severity(art, X)[0])
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m model.predict <drug_a> <drug_b>")
        sys.exit(1)
    print(predict(sys.argv[1], sys.argv[2]))