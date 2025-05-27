import streamlit as st
import pandas as pd
from utils.annotation_helpers import load_session, save_session

DATA_PATH = "data/sample_with_llm_suggestions.csv"

st.set_page_config(layout="wide")
st.title("📝 Political Corruption Annotation Tool")

# ========== User Login ==========
user_id = st.text_input("Enter your username (for saving progress):")

if not user_id:
    st.stop()

session_data = load_session(user_id)

# ========== Load Data ==========
@st.cache_data
def load_articles():
    return pd.read_csv(DATA_PATH)

df = load_articles()
total_articles = len(df)

# Find current index
current_index = session_data.get("last_index", 0)

if current_index >= total_articles:
    st.success("✅ You have completed all articles!")
    st.stop()

row = df.iloc[current_index]

# ========== Display Article ==========
st.subheader(f"Article {current_index + 1} of {total_articles}")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Original Text**")
    st.write(row.get("original_text", ""))

with col2:
    st.markdown("**Translated Text**", unsafe_allow_html=True)
    st.markdown(row.get("translated_text", ""), unsafe_allow_html=True)

st.markdown("---")
st.markdown("**LLM Suggestions**")
st.markdown(f"**Rationale:** _{row.get('llm_rationale', '')}_")
st.markdown(f"**Evidence:** {row.get('llm_evidence', '')}")

# ========== Annotation Form ==========
st.markdown("### Your Label")
label = st.radio(
    "Does this article primarily concern political corruption?",
    ["Yes", "Mentioned but not central", "No", "Unsure"]
)

notes = st.text_area("Comments (optional):")

if st.button("Save and Continue"):
    entry = {
        "article_index": current_index,
        "tentative_label": label,
        "notes": notes,
        "original_text": row.get("original_text", ""),
        "translated_text": row.get("translated_text", "")
    }

    # Save to session
    annotations = session_data.get("annotations", [])
    annotations.append(entry)
    session_data["annotations"] = annotations
    session_data["last_index"] = current_index + 1
    save_session(user_id, session_data)

    st.success("Saved! Reloading next article...")
    st.experimental_rerun()
