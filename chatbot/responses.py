"""
Turn a predict() result into a short, plain-language answer.

These are fixed templates, not an LLM, so the chatbot can never invent an
interaction: every sentence comes from the data or the model's output.
"""

FOOTER = "\n\n_MedCheck is not medical advice. Always check with your doctor or pharmacist._"

SEVERITY_TEXT = {
    "Major": (
        "🔴",
        "This combination can be dangerous. Don't take them together "
        "without talking to your doctor or pharmacist first.",
    ),
    "Moderate": (
        "🟠",
        "They may need monitoring or a dose change when taken together. "
        "Ask your pharmacist before combining them.",
    ),
    "Minor": (
        "🟡",
        "Usually low risk, but mention it to your pharmacist.",
    ),
}


# DrugBank effect type -> plain language. Anything not listed is shown as-is.
EFFECT_TEXT = {
    "metabolism": "how the body breaks down one of the drugs (metabolism)",
    "serum concentration": "the level of one of the drugs in the blood",
    "therapeutic efficacy": "how well one of the drugs works",
    "absorption": "how well one of the drugs is absorbed",
    "excretion rate": "how fast one of the drugs leaves the body",
    "risk or severity of bleeding": "the risk of bleeding",
    "anticoagulant activities": "blood thinning (anticoagulant effect)",
    "risk or severity of adverse effects": "the risk of side effects",
    "QTc-prolonging activities": "heart rhythm (QT prolongation)",
    "cardiotoxic activities": "heart toxicity",
    "hypotensive activities": "blood pressure lowering",
    "hypertensive activities": "blood pressure raising",
    "hypoglycemic activities": "blood sugar lowering",
    "hyperkalemic activities": "potassium levels in the blood",
    "bradycardic activities": "heart rate slowing",
    "nephrotoxic activities": "kidney toxicity",
    "hepatotoxic activities": "liver toxicity",
    "CNS depressant activities": "central nervous system depression",
    "central nervous system depressant (CNS depressant) activities":
        "central nervous system depression (drowsiness, slowed reactions)",
    "antihypertensive activities": "blood pressure lowering",
    "sedative activities": "sedation",
    "serotonergic activities": "serotonin activity",
}


def describe_effects(effects: list[str]) -> str:
    parts = [EFFECT_TEXT.get(e, e) for e in effects[:3]]
    text = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"\n\n**What can happen:** this combination can affect {text} (source: DrugBank)."


def answer_style(r: dict) -> str:
    """Which colored box to show the answer in: error, warning, info or success."""
    if r.get("status") != "ok":
        return "info"
    if r["source"] == "DDInter":
        return {"Major": "error", "Moderate": "warning"}.get(r["severity"], "info")
    if not r["interaction"]:
        return "success"
    return "error" if r.get("estimated_severity") == "Major" else "warning"


def format_answer(r: dict) -> str:
    text = _main_answer(r)
    if r.get("effects"):
        body, _, footer = text.partition(FOOTER)
        text = body + describe_effects(r["effects"]) + FOOTER
    return text


def _main_answer(r: dict) -> str:
    status = r.get("status")

    if status == "unknown_drug":
        names = ", ".join(f"**{n}**" for n in r["unknown"])
        return (
            f"I couldn't find {names} in our data. Check the spelling, or try the "
            "generic name (for example *ibuprofen* instead of a brand name)." + FOOTER
        )

    if status == "same_drug":
        return (
            f"**{r['drug_a']}** and **{r['drug_b']}** look like the same medicine. "
            "Taking two products with the same ingredient can mean a double dose. "
            "Ask your pharmacist." + FOOTER
        )

    a, b = f"**{r['drug_a']}**", f"**{r['drug_b']}**"

    if r["source"] == "DDInter":
        if r["severity"] == "Unrated":
            return (
                f"⚪ **Known interaction, severity not rated.** DDInter lists an "
                f"interaction between {a} and {b} but doesn't rate how serious it is. "
                f"Our model's estimate: likely **{r['estimated_severity']}**. "
                "Ask your pharmacist before combining them." + FOOTER
            )
        icon, advice = SEVERITY_TEXT[r["severity"]]
        return (
            f"{icon} **{r['severity']} interaction** between {a} and {b} "
            f"(source: DDInter). {advice}" + FOOTER
        )

    if r["source"] == "DrugBank":
        return (
            f"🟠 **Interaction listed in DrugBank.** {a} and {b} are not listed "
            f"together in DDInter, but DrugBank lists an interaction between them. "
            f"Our model's severity estimate: **{r['estimated_severity']}**. "
            "Ask your pharmacist before combining them." + FOOTER
        )

    # Not in DDInter or DrugBank: model estimate
    pct = round(r["probability"] * 100)
    if r["interaction"]:
        return (
            f"🟠 **Possible interaction (prediction).** {a} and {b} are not listed "
            f"together in DDInter, but our model estimates a {pct}% chance of an "
            f"interaction, above our {round(r['threshold'] * 100)}% safety threshold. "
            f"Estimated severity: **{r['estimated_severity']}**. This is a "
            "prediction, not a confirmed interaction. Ask your pharmacist." + FOOTER
        )
    return (
        f"🟢 **No known interaction** between {a} and {b} in DDInter. Our model "
        f"estimates a {pct}% chance of an interaction, below our "
        f"{round(r['threshold'] * 100)}% safety threshold. "
        "This doesn't guarantee they're safe together." + FOOTER
    )