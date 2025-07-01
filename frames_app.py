import streamlit as st
import pandas as pd
import os
import csv
import json
import numpy as np
from typing import List
import string

# === File paths ===
ANNOTATION_FILE = "annotations.csv"
DATA_PATH = "data/news_sample_with_7_frames.csv"
SESSION_FOLDER = "sessions"

# === Frame labels ===
FRAME_LABELS = [
    "Foreign influence threat",
    "Systemic institutional corruption",
    "Elite collusion",
    "Politicized investigations",
    "Authoritarian reformism",
    "Judicial and institutional accountability failures",
    "Mobilizing anti-corruption"
]

# === Load/save session ===
def load_session(user_id):
    path = os.path.join(SESSION_FOLDER, f"{user_id}_session.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_session(user_id, session_data):
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        raise TypeError(f"Unserializable object {obj} of type {type(obj)}")

    os.makedirs(SESSION_FOLDER, exist_ok=True)
    path = os.path.join(SESSION_FOLDER, f"{user_id}_session.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, default=convert)

# === Load articles ===
@st.cache_data
def load_articles():
    return pd.read_csv(DATA_PATH)

def fallback_session(user_id):
    return {"user_id": user_id, "current_index": 0, "annotations": []}

def safe_load_session(user_id):
    os.makedirs(SESSION_FOLDER, exist_ok=True)
    try:
        return load_session(user_id)
    except (json.JSONDecodeError, FileNotFoundError):
        return fallback_session(user_id)

# === Save annotation to CSV ===
def save_annotation(entry: dict):
    annotations = []
    if os.path.exists(ANNOTATION_FILE):
        try:
            with open(ANNOTATION_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                annotations = list(reader)
        except Exception as e:
            print(f"❌ Error reading annotation file: {e}")

    # Remove existing for the same user/article
    annotations = [
        a for a in annotations
        if not (a["user_id"] == entry["user_id"] and a["article_index"] == str(entry["article_index"]))
    ]
    annotations.append(entry)

    fieldnames = [
        'user_id', 'article_index', 'notes', 'flagged',
        'uri', 'original_text', 'translated_text'
    ] + [f"{label}_present" for label in FRAME_LABELS]

    try:
        with open(ANNOTATION_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotations)
    except Exception as e:
        print(f"❌ Error writing annotation file: {e}")

# === Streamlit UI ===
def main():
    st.set_page_config(layout="wide")
    st.title("📝 Frame Classification Annotation Tool")

    user_id = st.text_input("Enter your username:")
    if not user_id:
        st.info("Please enter your username to continue.")
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Text**")
        st.write(row.get("combined_text", ""))

    with col2:
        st.markdown("**Translated Text**")
        st.write(row.get("translated_text", ""))

    st.markdown("---")
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

# Run app
if __name__ == "__main__":
    main()
