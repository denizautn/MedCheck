"""
Add "what happens" to each drug pair, from DrugBank (via Mendeley Data).

Input:  data/raw/drugbank/DDI_data.csv
        columns: drug1_id, drug2_id, drug1_name, drug2_name, interaction_type
        data/processed/interactions.csv   (from prepare_data.py, for DDInter IDs)
Output: data/processed/effects.csv
        columns: DDInterID_A, DDInterID_B, effects   (effects joined with "; ")

DrugBank only gives what is affected (e.g. "risk or severity of bleeding"),
not whether it goes up or down, so the app says "can affect", never
"increases" or "decreases".

Source: Mendeley Data, "Data of multiple-type drug-drug interactions"
(doi:10.17632/md5czfsfnd.1, CC BY 4.0), extracted from DrugBank 5.1.

Run from the project folder (after prepare_data.py):
    python -m model.prepare_effects
"""

from pathlib import Path

import pandas as pd

DRUGBANK_PATH = Path("data/raw/drugbank/DDI_data.csv")
INTERACTIONS_PATH = Path("data/processed/interactions.csv")
OUT_PATH = Path("data/processed/effects.csv")


def main() -> None:
    db = pd.read_csv(DRUGBANK_PATH)
    print(f"DrugBank pairs: {len(db):,}")

    ddi = pd.read_csv(INTERACTIONS_PATH)
    name_to_id = {n.lower().strip(): i for i, n in zip(ddi["DDInterID_A"], ddi["Drug_A"])}
    name_to_id.update(
        {n.lower().strip(): i for i, n in zip(ddi["DDInterID_B"], ddi["Drug_B"])}
    )

    db["id_a"] = db["drug1_name"].astype(str).str.lower().str.strip().map(name_to_id)
    db["id_b"] = db["drug2_name"].astype(str).str.lower().str.strip().map(name_to_id)
    db["effect"] = db["interaction_type"].astype(str).str.strip()

    drugs_db = set(db["drug1_name"].str.lower()) | set(db["drug2_name"].str.lower())
    drugs_matched = {n for n in drugs_db if n in name_to_id}
    print(f"DrugBank drugs found in DDInter: {len(drugs_matched):,} of {len(drugs_db):,}")

    db = db.dropna(subset=["id_a", "id_b"])
    db = db[db["id_a"] != db["id_b"]]

    # Same pair order as prepare_data.py: smaller ID first.
    a = db[["id_a", "id_b"]].min(axis=1)
    b = db[["id_a", "id_b"]].max(axis=1)
    db = db.assign(DDInterID_A=a, DDInterID_B=b)

    effects = (
        db.groupby(["DDInterID_A", "DDInterID_B"])["effect"]
        .agg(lambda s: "; ".join(sorted(set(s))))
        .reset_index()
        .rename(columns={"effect": "effects"})
    )

    known = set(zip(ddi["DDInterID_A"], ddi["DDInterID_B"]))
    in_ddinter = sum((x, y) in known for x, y in zip(effects["DDInterID_A"], effects["DDInterID_B"]))
    print(f"Pairs with an effect: {len(effects):,}")
    print(f"  also in DDInter:    {in_ddinter:,}")
    print(f"  only in DrugBank:   {len(effects) - in_ddinter:,}")
    print("Most common effects:")
    print(db["effect"].value_counts().head(10).to_string())

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    effects.to_csv(OUT_PATH, index=False)
    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
