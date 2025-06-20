import streamlit as st
import pandas as pd
import os
import csv
import re
import json
import numpy as np
from typing import List

ANNOTATION_FILE = "annotations.csv"
DATA_PATH = "data/news_sample_with_7_frames.csv"
SESSION_FOLDER = "sessions"  # folder to save user session files

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
    "frame_1_evidence": "#ffe8cc",
    "frame_2_evidence": "#ccf2ff",
    "frame_3_evidence": "#e6ccff",
    "frame_4_evidence": "#d5f5e3",
    "frame_5_evidence": "#ffcccc",
    "frame_6_evidence": "#ffffcc",
    "frame_7_evidence": "#f8d7da"
}

# --- Session helpers ---

def convert_to_native(obj):
    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def save_session(user_id: str, session_data: dict):
    session_data = convert_to_native(session_data)

    os.makedirs(SESSION_FOLDER, exist_ok=True)
    session_path = os.path.join(SESSION_FOLDER, f"{user_id}_session.json")

    try:
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
        print(f"✅ Session saved locally at: {session_path}")
    except Exception as e:
        print(f"❌ Error saving session locally: {e}")

def load_session(user_id: str):
    session_path = os.path.join(SESSION_FOLDER, f"{user_id}_session.json")
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        return session_data
    except Exception as e:
        print(f"❌ Error loading session for {user_id}: {e}")
        return {"user_id": user_id, "current_index": 0, "annotations": []}

# --- Your original functions ---

@st.cache_data
def load_articles():
    return pd.read_csv(DATA_PATH)

def fallback_session(user_id):
    return {"user_id": user_id, "current_index": 0, "annotations": []}

def safe_load_session(user_id):
    try:
        return load_session(user_id)
    except (json.JSONDecodeError, FileNotFoundError):
        return fallback_session(user_id)

def save_annotation(entry: dict):
    annotations = []
    if os.path.exists(ANNOTATION_FILE):
        try:
            with open(ANNOTATION_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                annotations = list(reader)
        except Exception as e:
            print(f"❌ Error reading local annotation file: {e}")

    annotations = [a for a in annotations if not (a["user_id"] == entry["user_id"] and a["article_index"] == str(entry["article_index"]))]
    annotations.append(entry)

    fieldnames = [
        'user_id', 'article_index', 'notes', 'flagged',
        'uri', 'original_text', 'translated_text'
    ] + [f"{label}_present" for label in FRAME_LABELS]

    try:
        with open(ANNOTATION_FILE, mode="w", newline="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotations)
        print(f"✅ Saved local annotation file: {ANNOTATION_FILE}")
    except Exception as e:
        print(f"❌ Error writing local annotation file: {e}")

    # Removed shared folder saving here per your request

def highlight_multiple_frames(text: str, evidence_dict: dict) -> str:
    if not isinstance(text, str):
        return ""

    highlights = []
    for col, phrases in evidence_dict.items():
        color = FRAME_COLORS.get(col, "#eeeeee")
        for phrase in phrases:
            if phrase.strip():
                highlights.append((phrase.strip(), color))

    highlights.sort(key=lambda x: -len(x[0]))

    parts = re.split(r'(<[^>]+>)', text)
    for i, part in enumerate(parts):
        if not part.startswith("<"):
            for phrase, color in highlights:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                part = pattern.sub(
                    fr"<span style='background-color: {color}; padding: 2px; border-radius: 4px;'>\g<0></span>",
                    part, count=1
                )
            parts[i] = part
    return "".join(parts)

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

    sess = safe_load_session(user_id)
    df = load_articles()
    total = len(df)
    current = sess.get("current_index", 0)

    if current >= total:
        st.success("✅ You have completed all articles!")
        st.stop()

    row = df.iloc[current]

    st.subheader(f"Article {current + 1} of {total}")
    st.number_input(
        "Jump to Article",
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
        st.markdown(
            f"<div style='height:300px; overflow-y: scroll; border:1px solid #ddd; padding:10px'>{highlighted}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 🤖 LLM Rationale")
    rationale = row.get("llm_rationale", "")
    st.markdown(highlight_keywords(rationale, KEY_TERMS), unsafe_allow_html=True)

    st.markdown("### 🏷️ Frame Presence")
    frame_selections = {}
    for label in FRAME_LABELS:
        frame_selections[label] = st.radio(
            f"{label}:", ["Not Present", "Present"], horizontal=True, key=f"{label}_radio"
        )

    notes = st.text_area("📝 Comments (optional):", key="notes")
    flagged = st.checkbox("🚩 Flag this article for review", key="flagged")

    col_prev, col_next = st.columns(2)

    with col_prev:
        if st.button("⬅️ Previous") and current > 0:
            sess["current_index"] = current - 1
            save_session(user_id, sess)
            st.rerun()

    with col_next:
        if st.button("Next ➡️"):
            entry = {
                "user_id": user_id,
                "article_index": current,
                "notes": notes,
                "flagged": str(flagged),
                "uri": row.get("uri", ""),
                "original_text": row.get("original_text", ""),
                "translated_text": row.get("translated_text", "")
            }
            for label in FRAME_LABELS:
                entry[f"{label}_present"] = frame_selections[label]

            existing = sess.get("annotations", [])
            existing = [a for a in existing if a["article_index"] != current]
            existing.append(entry)
            sess["annotations"] = existing

            save_annotation(entry)

            sess["current_index"] = current + 1
            save_session(user_id, sess)
            st.rerun()

if __name__ == "__main__":
    main()
