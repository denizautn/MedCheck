"""
MedCheck chat interface.

Run from the project folder:
    streamlit run app.py
"""

import streamlit as st

from chatbot.responses import FOOTER, answer_style, format_answer
from model.predict import get_matcher, load, predict

# From results/metrics.txt (safety thresholds). Update if you retrain.
MAJOR_RECALL = "92.6%"

EXAMPLES = [
    ("Warfarin + Aspirin", "Can I take warfarin with aspirin?"),
    ("Coumadin + Advil", "My grandma takes Coumadin and Advil every day"),
    ("Lipitor + Cordarone", "Can my dad take Lipitor with Cordarone?"),
    ("Tylenol + Zoloft", "Is Tylenol okay with Zoloft?"),
]

st.set_page_config(page_title="MedCheck", page_icon="💊")


@st.cache_resource
def data_counts() -> tuple[int, int]:
    _, lookup, matcher = load()
    return len(matcher.choices), len(lookup)


# ---------- Sidebar ----------
with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. **You ask** about two medicines, by brand or generic name.\n"
        "2. **MedCheck matches** the names to DDInter (typos and 130+ brand names).\n"
        "3. **Known pair?** We answer straight from the DDInter database.\n"
        "4. **Unknown pair?** MedCheck estimates the risk, tuned to catch "
        "dangerous interactions.\n"
        "5. **Everything runs on your device.** No internet, no one sees "
        "what you take."
    )
    st.header("Severity levels")
    st.markdown(
        "🔴 **Major**: avoid unless your doctor says otherwise\n\n"
        "🟠 **Moderate**: may need monitoring or a dose change\n\n"
        "🟡 **Minor**: usually low risk\n\n"
        "⚪ **Unrated**: known interaction, no severity in the data\n\n"
        "🟢 **None known**: not in DDInter, low model estimate"
    )
    st.divider()
    st.caption(
        "Data: Data: DDInter (CC BY-NC-SA 4.0) and DrugBank 5.1 interaction types via Mendeley Data (CC BY 4.0). MedCheck is a student project and not medical advice. MedCheck is for a hackathon project lol dont take it as medical advice. Always check with your doctor or pharmacist. MedCheck is not a chatbot, it's a lookup tool for a drug interaction database, and a model trained to catch dangerous interactions. It's "
        "not medical advice."
    )
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------- Header ----------
st.title("MedCheck")
st.markdown(
    "**Check if two medicines are safe to take together.** Answers come from "
    "a drug interaction database, it's not a chatbot guessing."
    "" \
    " Opsec: no internet, no one can possibly see what you take."
)

n_drugs, n_pairs = data_counts()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Drugs", f"{n_drugs:,}")
c2.metric("Known interactions", f"{n_pairs:,}")
c3.metric("Major risks caught", MAJOR_RECALL)
st.divider()

# ---------- Chat ----------
if "messages" not in st.session_state:
    st.session_state.messages = []


def answer(prompt: str) -> dict:
    drugs = get_matcher().find_in_message(prompt)
    if len(drugs) < 2:
        if drugs:
            text = (
                f"I found **{drugs[0]}**, but I need two medicines. "
                "Which other medicine are you taking?"
            )
        else:
            text = (
                "I couldn't find two medicine names in your message. Try "
                "something like: *Can I take warfarin with aspirin?*"
            )
        return {"role": "assistant", "content": text, "style": None, "details": None}
    details = predict(drugs[0], drugs[1])
    return {
        "role": "assistant",
        "content": format_answer(details),
        "style": answer_style(details),
        "details": details,
    }


def show(msg: dict) -> None:
    avatar = "💊" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        style = msg.get("style")
        if style:
            body, _, footer = msg["content"].partition(FOOTER)
            getattr(st, style)(body)
            if footer or FOOTER in msg["content"]:
                st.caption(FOOTER.strip().strip("_"))
        else:
            st.markdown(msg["content"])
        if msg.get("details"):
            with st.expander("How we got this answer"):
                st.json(msg["details"])


if not st.session_state.messages:
    with st.chat_message("assistant", avatar="💊"):
        st.markdown(
            "Hi! Tell me two medicines and I'll check if they interact. "
            "Try one of these:"
        )
        cols = st.columns(len(EXAMPLES))
        for col, (label, question) in zip(cols, EXAMPLES):
            if col.button(label, use_container_width=True):
                st.session_state.pending = question
                st.rerun()

for msg in st.session_state.messages:
    show(msg)

prompt = st.chat_input("Ask about two medicines...") or st.session_state.pop("pending", None)
if prompt:
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    show(user_msg)
    reply = answer(prompt)
    st.session_state.messages.append(reply)
    show(reply)