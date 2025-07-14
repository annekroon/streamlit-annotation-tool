import streamlit as st
import pandas as pd
import os
import csv
import json
import numpy as np

# === CONFIG ===
ANNOTATION_FILE = "annotations.csv"
DATA_PATH = "data/news_sample_with_7_frames.csv"
SESSION_FOLDER = "sessions"

FRAME_LABELS = [
    "Foreign influence threat",
    "Systemic institutional corruption",
    "Elite collusion",
    "Politicized investigations",
    "Authoritarian reformism",
    "Judicial and institutional accountability failures",
    "Mobilizing anti-corruption"
]

FRAME_COLORS = {
    f"frame_{i}_evidence": color for i, color in enumerate([
        "#cce5ff", "#d5f5e3", "#e6ccff", "#ffe8cc", "#ffcccc", "#f8d7da", "#ffffcc"
    ], start=1)
}

# === HELPERS ===
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

def save_annotation(entry: dict):
    annotations = []
    if os.path.exists(ANNOTATION_FILE):
        try:
            with open(ANNOTATION_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                annotations = list(reader)
        except Exception as e:
            print(f"❌ Error reading annotation file: {e}")

    annotations = [a for a in annotations if not (a["user_id"] == entry["user_id"] and a["article_index"] == str(entry["article_index"]))]
    annotations.append(entry)

    fieldnames = [
        'user_id', 'article_index', 'notes', 'flagged',
        'uri', 'original_text', 'translated_text',
        'political_corruption'
    ] + [f"{label}_present" for label in FRAME_LABELS]

    try:
        with open(ANNOTATION_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotations)
    except Exception as e:
        print(f"❌ Error writing annotation file: {e}")

def collect_current_annotation(user_id, current, row):
    entry = {
        "user_id": user_id,
        "article_index": current,
        "notes": st.session_state.get("notes", ""),
        "flagged": str(st.session_state.get("flagged", False)),
        "uri": row.get("uri", ""),
        "original_text": row.get("original_text", ""),
        "translated_text": row.get("translated_text", ""),
        "political_corruption": st.session_state.get("political_corruption", "No")
    }
    for label in FRAME_LABELS:
        entry[f"{label}_present"] = st.session_state.get(f"{label}_radio", "Not Present")
    return entry

def jump_to(index: int, sess, user_id, row, current):
    entry = collect_current_annotation(user_id, current, row)
    existing = sess.get("annotations", [])
    existing = [a for a in existing if a["article_index"] != current]
    existing.append(entry)
    sess["annotations"] = existing
    save_annotation(entry)

    sess["current_index"] = index
    save_session(user_id, sess)
    st.session_state["frames_prepopulated"] = False
    st.rerun()

# === MAIN APP ===
def main():
    st.set_page_config(layout="wide")
    st.title("📝 Corruption Frame Annotation Tool")

    if "user_id" not in st.session_state:
        user_id = st.selectbox("Select your username:", ["Assia", "Alexander", "Elisa", "Luigia", "Yara", "Anne"])
        if st.button("Start annotating"):
            st.session_state["user_id"] = user_id
            st.rerun()
        st.stop()

    user_id = st.session_state["user_id"]
    sess = safe_load_session(user_id)
    df = load_articles()
    total = len(df)
    current = sess.get("current_index", 0)

    if current >= total:
        st.success("✅ You have completed all articles!")

        if st.button("⬅️ Go back to previous article"):
            sess["current_index"] = total - 1
            save_session(user_id, sess)
            st.session_state["reset_frames"] = True
            st.session_state["frames_prepopulated"] = False
            st.rerun()

        st.stop()

    row = df.iloc[current]

    st.subheader(f"Article {current + 1} of {total}")
    st.number_input(
        "Jump to Article",
        0, total - 1, current,
        key="nav",
        on_change=lambda: jump_to(st.session_state.nav, sess, user_id, row, current)
    )

    existing_annotation = next((a for a in sess.get("annotations", []) if a["article_index"] == current), None)

    if existing_annotation and not st.session_state.get("frames_prepopulated", False):
        for label in FRAME_LABELS:
            st.session_state[f"{label}_radio"] = existing_annotation.get(f"{label}_present", "Not Present")
        st.session_state["political_corruption"] = existing_annotation.get("political_corruption", "No")
        st.session_state["notes"] = existing_annotation.get("notes", "")
        st.session_state["flagged"] = existing_annotation.get("flagged", "False") == "True"
        st.session_state["frames_prepopulated"] = True

    if st.session_state.get("reset_frames", False):
        for label in FRAME_LABELS:
            st.session_state[f"{label}_radio"] = "Not Present"
        st.session_state["notes"] = ""
        st.session_state["flagged"] = False
        st.session_state["reset_frames"] = False

    for label in FRAME_LABELS:
        if f"{label}_radio" not in st.session_state:
            st.session_state[f"{label}_radio"] = "Not Present"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Text**")
        st.write(row.get("combined_text", ""))

    with col2:
        st.markdown("**Translated Text**")
        st.write(row.get("translated_text", ""))

    st.markdown("### 🧠 Frame-wise rationale & evidence")
    for i in range(1, 8):
        col_name = f"frame_{i}_evidence"
        rationale_col = f"frame_{i}_rationale"
        frame_label = FRAME_LABELS[i - 1]
        color = FRAME_COLORS.get(col_name, "#eeeeee")

        evidence_text = str(row.get(col_name, "")).strip()
        rationale_text = str(row.get(rationale_col, "")).strip()

        if evidence_text or rationale_text:
            st.markdown(
                f"<div style='margin-top:10px; padding:10px; border-left: 6px solid {color}; "
                f"background-color:{color}33;'>"
                f"<b style='color:{color};'>🟩 {frame_label}</b><br><br>"
                f"<i><u>Rationale:</u></i><br> {rationale_text or '—'}<br><br>"
                f"<i><u>Evidence:</u></i> {evidence_text or '—'}"
                f"</div>",
                unsafe_allow_html=True
            )

    st.markdown("### 🏷️ Frame presence")
    frame_selections = {}
    for label in FRAME_LABELS:
        frame_selections[label] = st.radio(f"{label}:", ["Not Present", "Present"], horizontal=True, key=f"{label}_radio")

    st.markdown("### 🗳️ Is this article primarily about political corruption?")
    political_corruption = st.radio("Your answer:", ["Yes", "No"], horizontal=True, key="political_corruption")

    notes = st.text_area("📝 Comments (optional):", key="notes")
    flagged = st.checkbox("🚩 Flag this article for review", key="flagged")

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Previous") and current > 0:
            entry = collect_current_annotation(user_id, current, row)
            existing = sess.get("annotations", [])
            existing = [a for a in existing if a["article_index"] != current]
            existing.append(entry)
            sess["annotations"] = existing
            save_annotation(entry)

            sess["current_index"] = current - 1
            save_session(user_id, sess)
            st.session_state["reset_frames"] = True
            st.session_state["frames_prepopulated"] = False
            st.rerun()

    with col_next:
        if st.button("Next ➡️"):
            entry = collect_current_annotation(user_id, current, row)
            existing = sess.get("annotations", [])
            existing = [a for a in existing if a["article_index"] != current]
            existing.append(entry)
            sess["annotations"] = existing

            save_annotation(entry)
            sess["current_index"] = current + 1
            save_session(user_id, sess)
            st.session_state["reset_frames"] = True
            st.session_state["frames_prepopulated"] = False
            st.rerun()

if __name__ == "__main__":
    main()
