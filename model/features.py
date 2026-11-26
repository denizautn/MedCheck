"""
Turn a drug pair into numbers the model can learn from.

DDInter only gives drug names, so we describe each drug by its known
interactions:
  - how many interactions it has (scaled by the size of the data)
  - what share of them are Minor / Moderate / Major / Unknown
and each pair by how many interaction partners the two drugs share.

Out-of-fold: training features must never be built from data that includes
the pair itself, or the model memorizes the answer. So the training set is
split into K folds, and each fold's features come from the other folds only.
Test pairs and new pairs use statistics from the whole training set.
"""

import numpy as np
import pandas as pd

LEVELS = ["Minor", "Moderate", "Major", "Unknown"]
LEVEL_INDEX = {level: i for i, level in enumerate(LEVELS)}
SCALE = 10_000  # degrees are reported per 10,000 known pairs

FEATURE_NAMES = (
    ["degree_min", "degree_max", "common_partners", "jaccard"]
    + [f"share_sum_{l}" for l in LEVELS]
    + [f"share_max_{l}" for l in LEVELS]
    + [f"share_min_{l}" for l in LEVELS]
)


class DrugStats:
    """Interaction counts and partners for every drug, from known pairs."""

    def __init__(self, positives: pd.DataFrame):
        counts: dict[str, np.ndarray] = {}
        partners: dict[str, set] = {}
        for a, b, level in zip(
            positives["DDInterID_A"], positives["DDInterID_B"], positives["Level"]
        ):
            i = LEVEL_INDEX.get(level, LEVEL_INDEX["Unknown"])
            for drug, other in ((a, b), (b, a)):
                counts.setdefault(drug, np.zeros(len(LEVELS)))[i] += 1
                partners.setdefault(drug, set()).add(other)
        # Plain dicts and frozensets so the object can be saved with joblib.
        self.counts = counts
        self.partners = {d: frozenset(p) for d, p in partners.items()}
        self.n_pairs = max(len(positives), 1)

    def pair_features(self, a: str, b: str) -> list:
        empty = np.zeros(len(LEVELS))
        ca = self.counts.get(a, empty)
        cb = self.counts.get(b, empty)
        pa = self.partners.get(a, frozenset())
        pb = self.partners.get(b, frozenset())

        deg_a, deg_b = ca.sum(), cb.sum()
        share_a = ca / deg_a if deg_a > 0 else empty
        share_b = cb / deg_b if deg_b > 0 else empty

        common = len(pa & pb)
        union = len((pa | pb) - {a, b})
        jaccard = common / union if union > 0 else 0.0

        scale = SCALE / self.n_pairs
        return (
            [min(deg_a, deg_b) * scale, max(deg_a, deg_b) * scale, common * scale, jaccard]
            + list(share_a + share_b)
            + list(np.maximum(share_a, share_b))
            + list(np.minimum(share_a, share_b))
        )


def build_matrix(df: pd.DataFrame, stats: DrugStats) -> np.ndarray:
    """Features for pairs the stats were NOT built from (test or new pairs)."""
    return np.array(
        [stats.pair_features(a, b) for a, b in zip(df["DDInterID_A"], df["DDInterID_B"])],
        dtype=float,
    )


def build_oof_matrix(train: pd.DataFrame, k: int = 5, seed: int = 42) -> np.ndarray:
    """Out-of-fold features for the training set."""
    folds = np.random.default_rng(seed).integers(0, k, len(train))
    X = np.zeros((len(train), len(FEATURE_NAMES)))
    for f in range(k):
        held_out = folds == f
        rest = train[~held_out]
        stats = DrugStats(rest[rest["interaction"] == 1])
        X[held_out] = build_matrix(train[held_out], stats)
    return X
