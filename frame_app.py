# This version includes all fixes and restores frame color highlighting + robust JSON loading

import streamlit as st
import pandas as pd
import json
import os
import re
from annotated_text import annotated_text
from utils.rationale_generator import generate_frame_rationale

FRAME_LIST = [
    "Economic consequences",
    "Capacity and resources",
    "Morality",
    "Fairness and equality",
    "Legality, constitutionality and jurisprudence",
    "Policy prescription and evaluation",
    "Public opinion"
]

LOCAL_SESSION_DIR = ".annotations"

os.makedirs(LOCAL_SESSION_DIR, exist_ok=True)

def load_session(user_id):
    path = os.path.join(LOCAL_SESSION_DIR, f"{user_id}_session.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.warning("Corrupted session file found. Starting with a new session.")
            return {"annotations": []}
    else:
        return {"annotations": []}

def save_session(user_id, session_data):
    path = os.path.join(LOCAL_SESSION_DIR, f"{user_id}_session.json")
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2, default=str)

def color_highlight_text(text, rationale_map):
    spans = []
    cursor = 0

    color_palette = {
        "Economic consequences": "#ffadad",
        "Capacity and resources": "#ffd6a5",
        "Morality": "#fdffb6",
        "Fairness and equality": "#caffbf",
        "Legality, constitutionality and jurisprudence": "#9bf6ff",
        "Policy prescription and evaluation": "#a0c4ff",
        "Public opinion": "#bdb2ff"
    }

    for frame, rationale in rationale_map.items():
        if rationale:
            for match in re.finditer(re.escape(rationale), text, re.IGNORECASE):
                spans.append((match.start(), match.end(), frame))

    spans.sort()

    annotated = []
    last_idx = 0
    for start, end, frame in spans:
        if start > last_idx:
            annotated.append(text[last_idx:start])
        annotated.append((text[start:end], frame, color_palette[frame]))
        last_idx = end

    if last_idx < len(text):
        annotated.append(text[last_idx:])

    return annotated

def main():
    st.title("News Frame Annotation Tool")

    user_id = st.text_input("Enter your name/ID:", value="anon")
    if not user_id:
        st.stop()

    uploaded_file = st.file_uploader("Upload the news CSV file", type="csv")
    if not uploaded_file:
        st.stop()

    df = pd.read_csv(uploaded_file)
    if 'content' not in df.columns:
        st.error("CSV must contain a 'content' column")
        st.stop()

    sess = load_session(user_id)

    if "index" not in sess:
        sess["index"] = 0
    if "annotations" not in sess:
        sess["annotations"] = []

    idx = sess["index"]
    if idx >= len(df):
        st.success("Annotation completed 🎉")
        st.stop()

    row = df.iloc[idx]
    text = row['content']

    st.subheader("Article")

    rationale_map = {}
    for frame in FRAME_LIST:
        rationale = generate_frame_rationale(text, frame)
        rationale_map[frame] = rationale

    highlighted = color_highlight_text(text, rationale_map)
    annotated_text(*highlighted)

    st.subheader("Frame Presence Annotation")
    annotation = {"id": int(idx), "frames": {}, "rationales": {}}

    for frame in FRAME_LIST:
        col1, col2 = st.columns([2, 5])
        with col1:
            selected = st.selectbox(f"{frame} present?", ["not present", "present"], key=f"sel_{frame}")
        with col2:
            rationale_input = st.text_area(f"Optional rationale for {frame}", value=rationale_map[frame], key=f"rat_{frame}")

        annotation["frames"][frame] = selected
        annotation["rationales"][frame] = rationale_input if selected == "present" else ""

    if st.button("Next"):
        sess["annotations"].append(annotation)
        sess["index"] += 1
        save_session(user_id, sess)
        st.experimental_rerun()

if __name__ == "__main__":
    main()
