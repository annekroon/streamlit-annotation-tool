import streamlit as st
import pandas as pd
import os
import csv
import json
import numpy as np

# === CONFIG ===
ANNOTATION_FILE = "annotations_final.csv"
SESSION_FOLDER = "sessions_final"

# Mapping from coder names to their dataset paths.
# Real coders and test accounts point to the same underlying data.
USER_DATASET = {
    "Assia": "data/Netherlands_Assia_sample_250_llm_annotated.csv",
    "TestAssia": "data/Netherlands_Assia_sample_250_llm_annotated.csv",
    "Alexander": "data/Bulgaria_Alexander_sample_250_llm_annotated.csv",
    "TestAlexander": "data/Bulgaria_Alexander_sample_250_llm_annotated.csv",
    "Elisa": "data/United_Kingdom_Elisa_sample_250_llm_annotated.csv",
    "TestElisa": "data/United_Kingdom_Elisa_sample_250_llm_annotated.csv",
    "Luigia": "data/Italy_Luigia_sample_250_llm_annotated.csv",
    "TestLuigia": "data/Italy_Luigia_sample_250_llm_annotated.csv",
    # If Yara or Anne need a specific dataset, add them here.
}

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
        "#cce5ff", "#d5f5e3", "#e6ccff", "#ffe8cc",
        "#ffcccc", "#f8d7da", "#ffffcc"
    ], start=1)
}

# === HELPERS ===
def load_session(user_id):
    """Load a coder's session from disk."""
    path = os.path.join(SESSION_FOLDER, f"{user_id}_session.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_session(user_id, session_data):
    """Save a coder's session to disk."""
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

@st.cache_data(show_spinner=False)
def load_articles(data_path):
    """Read a CSV file into a DataFrame.  Cached per file path."""
    return pd.read_csv(data_path)

def fallback_session(user_id):
    """Create an empty session structure for a new user."""
    return {"user_id": user_id, "current_index": 0, "annotations": []}

def safe_load_session(user_id):
    """Load session data if it exists, otherwise create a blank session."""
    os.makedirs(SESSION_FOLDER, exist_ok=True)
    try:
        return load_session(user_id)
    except (json.JSONDecodeError, FileNotFoundError):
        return fallback_session(user_id)

def save_annotation(entry: dict):
    """Append or update one annotation in the CSV and write it back to disk."""
    annotations = []
    if os.path.exists(ANNOTATION_FILE):
        try:
            with open(ANNOTATION_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                annotations = list(reader)
        except Exception as e:
            print(f"❌ Error reading annotation file: {e}")

    # Remove previous annotation for this user/article combination
    annotations = [
        a for a in annotations
        if not (a["user_id"] == entry["user_id"] and a["article_index"] == str(entry["article_index"]))
    ]
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

def jump_to(index: int, sess, user_id):
    """Navigate to a particular article index and save session state."""
    sess["current_index"] = index
    save_session(user_id, sess)

# === MAIN APP ===
def main():
    st.set_page_config(layout="wide")
    st.title("📝 Corruption Frame Annotation Tool")

    # User login / selection
    if "user_id" not in st.session_state:
        # Real coders + test accounts
        user_choice = st.selectbox(
            "Select your username:",
            ["Assia", "Alexander", "Elisa", "Luigia", "Yara", "Anne",
             "TestAssia", "TestAlexander", "TestElisa", "TestLuigia"]
        )
        if st.button("Start annotating"):
            st.session_state["user_id"] = user_choice
            st.rerun()
        st.stop()

    user_id = st.session_state["user_id"]

    # Determine dataset based on user_id
    data_path = USER_DATASET.get(user_id)
    if data_path is None:
        st.error("No dataset configured for this user.")
        st.stop()

    # Load session and articles
    sess = safe_load_session(user_id)
    df = load_articles(data_path)
    total = len(df)
    current = sess.get("current_index", 0)

    if current >= total:
        st.success("✅ You have completed all articles!")

        if st.button("⬅️ Go back to previous article"):
            sess["current_index"] = total - 1
            save_session(user_id, sess)
            st.rerun()

        st.stop()

    row = df.iloc[current]

    # Header
    st.subheader(f"Article {current + 1} of {total}")

    # Jump-to navigation
    nav = st.number_input("Jump to Article", 0, total - 1, current, key="nav_input")
    if st.button("Go to article"):
        jump_to(int(nav), sess, user_id)
        st.rerun()

    # === RESET STATE WHEN ARTICLE CHANGES ===
    if st.session_state.get("last_loaded_index") != current:
        st.session_state["last_loaded_index"] = current
        # Reset frame radios, corruption, notes, flagged
        for label in FRAME_LABELS:
            st.session_state[f"{label}_radio"] = "Not Present"
        st.session_state["political_corruption"] = "Yes"
        st.session_state["notes"] = ""
        st.session_state["flagged"] = False

        # If this article has stored annotations, restore them
        stored = next((a for a in sess.get("annotations", []) if a["article_index"] == current), None)
        if stored:
            for label in FRAME_LABELS:
                st.session_state[f"{label}_radio"] = stored.get(f"{label}_present", "Not Present")
            st.session_state["political_corruption"] = stored.get("political_corruption", "No")
            st.session_state["notes"] = stored.get("notes", "")
            st.session_state["flagged"] = stored.get("flagged", "False") == "True"

    # === ARTICLE TEXT ===
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Text**")
        st.write(row.get("combined_text", ""))
    with col2:
        st.markdown("**Translated Text**")
        st.write(row.get("translated_text", ""))

    # === RATIONALE & CONFIDENCE DISPLAY ===
    st.markdown("### 🧠 Frame-wise rationale & confidence")
    for i in range(1, 8):
        name_col = f"frame_{i}_name"
        rationale_col = f"frame_{i}_rationale"
        confidence_col = f"frame_{i}_confidence"
        color = FRAME_COLORS.get(f"frame_{i}_evidence", "#eeeeee")

        frame_label_value = str(row.get(name_col, "")).strip()
        rationale_text = str(row.get(rationale_col, "")).strip()
        confidence_val_raw = row.get(confidence_col, "")

        try:
            confidence_float = float(confidence_val_raw)
        except (ValueError, TypeError):
            continue

        if (
            not rationale_text or rationale_text.lower() == "nan" or
            frame_label_value.lower() in ["none", "nan", ""] or
            frame_label_value.upper().startswith("NOT ")
        ):
            continue

        confidence_text = f"{confidence_float:.0f}"
        warning_icon = " ⚠️" if confidence_float < 90 else ""

        st.markdown(
            f"<div style='margin-top:10px; padding:10px; border-left: 6px solid {color}; "
            f"background-color:{color}33;'>"
            f"<b style='color:{color};'>🟩 {frame_label_value}</b><br><br>"
            f"<i><u>Rationale:</u></i><br> {rationale_text}<br><br>"
            f"<i><u>Confidence:</u></i> {confidence_text}{warning_icon}"
            f"</div>",
            unsafe_allow_html=True
        )

    # === FRAME PRESENCE ===
    st.markdown("### 🏷️ Frame presence")
    frame_selections = {}
    for label in FRAME_LABELS:
        frame_selections[label] = st.radio(
            f"{label}:", ["Not Present", "Present"], horizontal=True, key=f"{label}_radio"
        )

    # === POLITICAL CORRUPTION ===
    st.markdown("### 🗳️ Is this article primarily about political corruption?")
    political_corruption = st.radio(
        "Your answer:",
        ["Yes", "No"],
        horizontal=True,
        index=0,
        key="political_corruption"
    )

    # === NOTES + FLAG ===
    notes = st.text_area("📝 Comments (optional):", key="notes")
    flagged = st.checkbox("🚩 Flag this article for review", key="flagged")

    # === NAVIGATION ===
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
                "translated_text": row.get("translated_text", ""),
                "political_corruption": political_corruption
            }
            for label in FRAME_LABELS:
                entry[f"{label}_present"] = frame_selections[label]

            # Update session annotations
            existing = sess.get("annotations", [])
            existing = [a for a in existing if a["article_index"] != current]
            existing.append(entry)
            sess["annotations"] = existing

            # Persist annotation and session
            save_annotation(entry)
            sess["current_index"] = current + 1
            save_session(user_id, sess)
            st.rerun()

if __name__ == "__main__":
    main()
