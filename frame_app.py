import streamlit as st
import pandas as pd
import os
import csv
import re
from typing import List
import openpyxl
from utils.annotation_helpers import load_session, save_session

ANNOTATION_FILE = "annotations.csv"
DATA_PATH = "data/sample_with_llm_suggestions.csv"

KEY_TERMS = [
    "bribery", "embezzlement", "nepotism", "corruption", "fraud",
    "abuse of power", "favoritism", "money laundering", "kickback", "cronyism"
]

FRAME_LABELS = [
    "Political motive",
    "Institutional failure",
    "Individual greed",
    "Systemic corruption",
    "External influence",
    "Civic response",
    "Legal consequences",
    "No clear frame"
]

FRAME_COLORS = {
    "frame_1_evidence": "#ffe8cc",  # light orange
    "frame_2_evidence": "#ccf2ff",  # light blue
    "frame_3_evidence": "#e6ccff",  # light purple
    "frame_4_evidence": "#d5f5e3",  # light green
    "frame_5_evidence": "#ffcccc",  # light red
    "frame_6_evidence": "#ffffcc",  # light yellow
    "frame_7_evidence": "#f8d7da"   # light pink
}

def save_annotation(entry: dict):
    annotations = []
    if os.path.exists(ANNOTATION_FILE):
        try:
            with open(ANNOTATION_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                annotations = list(reader)
        except Exception as e:
            print(f"❌ Error reading local annotation file: {e}")

    annotations = [
        a for a in annotations
        if not (a["user_id"] == entry["user_id"] and a["article_index"] == str(entry["article_index"]))
    ]
    annotations.append(entry)

    fieldnames = [
        'user_id', 'article_index', 'frame_labels', 'notes', 'flagged',
        'uri', 'original_text', 'translated_text'
    ]

    try:
        with open(ANNOTATION_FILE, mode="w", newline="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotations)
        print(f"✅ Saved local annotation file: {ANNOTATION_FILE}")
    except Exception as e:
        print(f"❌ Error writing local annotation file: {e}")

    output_dir = "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations"
    try:
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, "annotations-fyp-yara.csv")
        with open(csv_path, mode="w", newline="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotations)
        print(f"✅ Saved CSV to: {csv_path}")

        excel_path = os.path.join(output_dir, "annotations-fyp-yara.xlsx")
        df = pd.DataFrame(annotations)
        df.to_excel(excel_path, index=False)
        print(f"✅ Saved Excel to: {excel_path}")

    except Exception as e:
        print(f"❌ Error saving annotations to shared folder: {e}")

def highlight_multiple_frames(text: str, evidence_dict: dict) -> str:
    if not isinstance(text, str):
        return ""
    for col, phrases in evidence_dict.items():
        if not isinstance(phrases, list):
            continue
        color = FRAME_COLORS.get(col, "#eeeeee")
        for hl in phrases:
            if not isinstance(hl, str) or not hl.strip():
                continue
            pattern = re.escape(hl.strip())
            regex = re.compile(pattern, re.IGNORECASE)
            text = regex.sub(
                fr"<span style='background-color: {color}; padding: 2px; border-radius: 4px;'>\g<0></span>",
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
    st.title("📝 Frame Classification Annotation Tool")

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
        evidence_dict = {}
        for i in range(1, 8):
            col_name = f"frame_{i}_evidence"
            val = row.get(col_name, "")
            if isinstance(val, str) and val.strip():
                evidence_dict[col_name] = [e.strip() for e in val.split(";") if e.strip()]

        highlighted = highlight_multiple_frames(raw_text, evidence_dict)
        highlighted = highlight_keywords(highlighted, KEY_TERMS)
        st.markdown(highlighted, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top: 10px;">
        <span style='background-color: #ffe8cc; padding: 2px 6px; border-radius: 4px;'>Frame 1</span>
        <span style='background-color: #ccf2ff; padding: 2px 6px; border-radius: 4px;'>Frame 2</span>
        <span style='background-color: #e6ccff; padding: 2px 6px; border-radius: 4px;'>Frame 3</span>
        <span style='background-color: #d5f5e3; padding: 2px 6px; border-radius: 4px;'>Frame 4</span>
        <span style='background-color: #ffcccc; padding: 2px 6px; border-radius: 4px;'>Frame 5</span>
        <span style='background-color: #ffffcc; padding: 2px 6px; border-radius: 4px;'>Frame 6</span>
        <span style='background-color: #f8d7da; padding: 2px 6px; border-radius: 4px;'>Frame 7</span>
        <span style='background-color: #cce5ff; padding: 2px 6px; border-radius: 4px;'>Keyword</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ Frame Label Definitions"):
        st.markdown("""
        - **Political motive**: Corruption described as driven by political goals.
        - **Institutional failure**: Emphasizes lack of oversight or governance.
        - **Individual greed**: Focus on personal financial gain.
        - **Systemic corruption**: Describes corruption as widespread or normalized.
        - **External influence**: Foreign actors or pressures involved.
        - **Civic response**: Focus on public outrage, protests, or activism.
        - **Legal consequences**: Judicial or legal repercussions.
        - **No clear frame**: Cannot be categorized confidently.
        """)

    st.markdown("---")
    st.markdown("**LLM Suggestions**")
    st.markdown(f"**Rationale:** _{row.get('llm_rationale', '')}_")

    frame_labels = st.multiselect(
        "Select all frames that apply to this article:",
        FRAME_LABELS,
        key="frame_labels"
    )

    notes = st.text_area("Comments (optional):", key="notes")
    flagged = st.checkbox("🚩 Flag this article for review (e.g., low quality, irrelevant, broken translation)", key="flagged")

    if st.button("Next"):
        entry = {
            "user_id": user_id,
            "article_index": current,
            "frame_labels": "; ".join(frame_labels),
            "notes": notes,
            "flagged": str(flagged),
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

