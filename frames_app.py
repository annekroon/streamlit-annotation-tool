import streamlit as st
import pandas as pd
import os
import csv

# ====== Configuration ======
FRAME_LABELS = ["Bribery", "Embezzlement", "Nepotism", "Election fraud"]
ANNOTATION_FILE = "annotations.csv"

# ====== Load Articles ======
@st.cache_data
def load_articles():
    return pd.read_csv("articles.csv")  # Must have columns: uri, original_text, translated_text

articles = load_articles()
article_count = len(articles)

# ====== Init Session State ======
if "article_index" not in st.session_state:
    st.session_state.article_index = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = []

# ====== Load Current Article ======
current = st.session_state.article_index
article = articles.iloc[current]

st.title("Political Corruption Annotation Tool")

st.markdown(f"**Article {current + 1} of {article_count}**")
st.markdown(f"**URI**: {article['uri']}")
st.markdown("### Translated Text")
st.text_area("Article Content", article["translated_text"], height=300, disabled=True)

# ====== Restore Previous Annotation if exists ======
previous_annotations = [
    a for a in st.session_state.annotations if a["article_index"] == current
]
if previous_annotations:
    prev = previous_annotations[0]
    for label in FRAME_LABELS:
        st.session_state[f"{label}_radio"] = prev.get(f"{label}_present", "Not Present")
    st.session_state["notes"] = prev.get("notes", "")
    st.session_state["flagged"] = prev.get("flagged", False)
    st.session_state["corruption_label_radio"] = prev.get("corruption_label", "Yes")
else:
    for label in FRAME_LABELS:
        st.session_state[f"{label}_radio"] = "Not Present"
    st.session_state["notes"] = ""
    st.session_state["flagged"] = False
    st.session_state["corruption_label_radio"] = "Yes"

# ====== Annotation Inputs ======
st.markdown("### Labels")
for label in FRAME_LABELS:
    st.radio(
        f"{label} present?",
        ["Present", "Not Present"],
        key=f"{label}_radio"
    )

st.markdown("### Is this article primarily about political corruption?")
corruption_label = st.radio(
    "Select one:",
    ["Yes", "No"],
    index=0,
    key="corruption_label_radio"
)

st.markdown("### Notes")
notes = st.text_area("Your notes (optional):", key="notes")

flagged = st.checkbox("Flag this article for review", key="flagged")

# ====== Save Annotations ======
def save_annotation():
    entry = {
        "user_id": "annotator_1",
        "article_index": current,
        "uri": article["uri"],
        "original_text": article["original_text"],
        "translated_text": article["translated_text"],
        "notes": st.session_state["notes"],
        "flagged": st.session_state["flagged"],
        "corruption_label": st.session_state["corruption_label_radio"]
    }
    for label in FRAME_LABELS:
        entry[f"{label}_present"] = st.session_state[f"{label}_radio"]

    # Remove existing annotation for this article
    st.session_state.annotations = [
        a for a in st.session_state.annotations if a["article_index"] != current
    ]
    st.session_state.annotations.append(entry)

    # Write to CSV
    fieldnames = [
        'user_id', 'article_index', 'notes', 'flagged',
        'uri', 'original_text', 'translated_text',
        'corruption_label'
    ] + [f"{label}_present" for label in FRAME_LABELS]

    with open(ANNOTATION_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in st.session_state.annotations:
            writer.writerow(row)

# ====== Navigation Buttons ======
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("⬅️ Previous", disabled=current == 0):
        save_annotation()
        st.session_state.article_index -= 1
        st.experimental_rerun()

with col2:
    if st.button("Next ➡️", disabled=current == article_count - 1):
        save_annotation()
        st.session_state.article_index += 1
        st.experimental_rerun()

with col3:
    article_jump = st.number_input("Jump to article:", min_value=1, max_value=article_count, step=1)
    if st.button("Go"):
        save_annotation()
        st.session_state.article_index = article_jump - 1
        st.experimental_rerun()

# ====== Final Save Button ======
st.markdown("---")
if st.button("💾 Save Annotations"):
    save_annotation()
    st.success("Annotations saved.")
