import streamlit as st
import pandas as pd
import os
import csv
import re
from typing import List
from utils.annotation_helpers import load_session, save_session

ANNOTATION_FILE = "annotations.csv"
#DATA_PATH = "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations/df_output_with_llm_annotations.csv"
DATA_PATH ="data/df_copy.csv"

KEY_TERMS = [
    "bribery", "embezzlement", "nepotism", "corruption", "fraud",
    "abuse of power", "favoritism", "money laundering", "kickback", "cronyism"
]

def save_annotation(entry: dict):
    annotations = []

    if os.path.exists(ANNOTATION_FILE):
        with open(ANNOTATION_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            annotations = list(reader)

    annotations = [
        a for a in annotations
        if not (a["user_id"] == entry["user_id"] and a["article_index"] == str(entry["article_index"]))
    ]
    annotations.append(entry)

    fieldnames = [
        'user_id', 'article_index', 'tentative_label', 'notes',
        'uri', 'original_text', 'translated_text'
    ]

    with open(ANNOTATION_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(annotations)

    output_dir = os.path.expanduser("~/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations")
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "annotations-fyp-yara.csv")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(annotations)

    excel_path = os.path.join(output_dir, "annotations-fyp-yara.xlsx")
    df = pd.DataFrame(annotations)
    df.to_excel(excel_path, index=False)

def highlight_translated_text(text: str, highlights: List[str]) -> str:
    if not isinstance(text, str):
        return ""
    for hl in highlights:
        if not isinstance(hl, str) or not hl.strip():
            continue
        pattern = re.escape(hl.strip())
        regex = re.compile(pattern, re.IGNORECASE)
        text = regex.sub(
            r"<span style='background-color: #ffe8cc; padding: 2px; border-radius: 4px;'>\g<0></span>",
            text,
            count=1
        )
    return text

def highlight_keywords(text: str, terms: List[str]) -> str:
    parts = re.split(r'(<[^>]+>)', text)
    for i, part in enumerate(parts):
        if not part.startswith("<"):
            for term in terms:
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                part = pattern.sub(
                    r"<span style='background-color: #cce5ff; padding: 2px; border-radius: 4px;'>\g<0></span>",
                    part
                )
            parts[i] = part
    return "".join(parts)

@st.cache_data
def load_articles():
    return pd.read_csv(DATA_PATH)

def jump_to(index: int, sess, user_id):
    sess["current_index"] = index
    save_session(user_id, sess)
    st.session_state["jump_requested"] = True

def main():
    st.set_page_config(layout="wide")
    st.title("📝 Political Corruption Annotation Tool")

    user_id = st.text_input("Enter your username:")
    if not user_id:
        st.stop()

    sess = load_session(user_id)
    df = load_articles()
    total = len(df)
    current = sess.get("current_index", 0)

    if "next_clicked" not in st.session_state:
        st.session_state.next_clicked = False
    if "jump_requested" not in st.session_state:
        st.session_state.jump_requested = False

    if current >= total:
        st.success("✅ You have completed all articles!")
        st.stop()

    row = df.iloc[current]

    st.subheader(f"Article {current + 1} of {total}")
    st.number_input(
        "Navigate Articles",
        0, total - 1, current,
        key="nav",
        on_change=lambda: jump_to(st.session_state.nav, sess, user_id)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Text**")
        st.write(row.get("original_text", ""))

    with col2:
        st.markdown("**Translated Text with Highlights**", unsafe_allow_html=True)
        raw_text = row.get("translated_text", "")
        llm_raw = row.get("llm_evidence", "")
        llm_evidence_list = []

        if isinstance(llm_raw, str):
            llm_evidence_list = [e.strip() for e in llm_raw.split(";") if e.strip()]

        highlighted = highlight_translated_text(raw_text, llm_evidence_list)
        highlighted = highlight_keywords(highlighted, KEY_TERMS)
        st.markdown(highlighted, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top: 10px;">
        <span style='background-color: #ffe8cc; padding: 2px 6px; border-radius: 4px;'>LLM Highlight</span>
        &nbsp;
        <span style='background-color: #cce5ff; padding: 2px 6px; border-radius: 4px;'>Keyword</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**LLM Suggestions**")
    st.markdown(f"**Rationale:** _{row.get('llm_rationale', '')}_")
    st.markdown(f"**Evidence:** {row.get('llm_evidence', '')}")

    label = st.radio(
        "Does this article primarily concern political corruption?",
        ["Yes", "Mentioned but not central", "No", "Unsure"],
        key="label"
    )

    notes = st.text_area("Comments (optional):", key="notes")

    if st.button("Next"):
        entry = {
            "user_id": user_id,
            "article_index": current,
            "tentative_label": label,
            "notes": notes,
            "uri": row.get("uri", ""),
            "original_text": row.get("original_text", ""),
            "translated_text": row.get("translated_text", "")
        }

        existing = sess.get("annotations", [])
        existing = [a for a in existing if a["article_index"] != current]
        existing.append(entry)
        sess["annotations"] = existing

        save_annotation(entry)

        sess["current_index"] = current + 1
        save_session(user_id, sess)

        st.session_state.next_clicked = True

    if st.session_state.next_clicked:
        st.session_state.next_clicked = False
        st.rerun()

    if st.session_state.jump_requested:
        st.session_state.jump_requested = False
        st.rerun()

if __name__ == "__main__":
    main()
