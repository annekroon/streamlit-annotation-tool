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

    # Reset frames and inputs if flagged for reset
    if st.session_state.get("reset_frames", False):
        for label in FRAME_LABELS:
            st.session_state[f"{label}_radio"] = "Not Present"
        st.session_state["notes"] = ""
        st.session_state["flagged"] = False
        st.session_state["reset_frames"] = False

    # Initialize frame selections to 'Not Present' if not set
    for label in FRAME_LABELS:
        if f"{label}_radio" not in st.session_state:
            st.session_state[f"{label}_radio"] = "Not Present"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Text**")
        st.write(row.get("combined_text", ""))

    with col2:
        st.markdown("**Translated Text with Highlights**", unsafe_allow_html=True)
        raw_text = row.get("translated_text", "")

        # ⬇️ Construct evidence dictionary for highlighting
        evidence_dict = {}
        for i in range(1, 8):
            col_name = f"frame_{i}_evidence"
            val = row.get(col_name, "")
            if isinstance(val, str) and val.strip():
                evidence_dict[col_name] = [e.strip() for e in val.split(";") if e.strip()]

        # ⬇️ Highlight text with frames and keywords
        highlighted = highlight_multiple_frames(raw_text, evidence_dict)
        highlighted = highlight_keywords(highlighted, KEY_TERMS)
        st.markdown(
            f"<div style='height:300px; overflow-y: scroll; border:1px solid #ddd; padding:10px'>{highlighted}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 🧠 Frame-wise Rationale & Evidence Highlights")

    for i in range(1, 8):
        col_name = f"frame_{i}_evidence"
        frame_label = FRAME_LABELS[i - 1]
        color = FRAME_COLORS.get(col_name, "#eeeeee")
        evidence_text = row.get(col_name, "").strip()

        if evidence_text:
            phrases = [p.strip() for p in evidence_text.split(";") if p.strip()]
            if phrases:
                st.markdown(
                    f"<div style='margin-top:10px; padding:10px; border-left: 6px solid {color}; "
                    f"background-color:{color}33;'>"
                    f"<b style='color:{color};'>🟩 {frame_label}</b><br>"
                    f"<i>Evidence Phrases:</i> {', '.join(phrases)}"
                    f"</div>",
                    unsafe_allow_html=True
                )

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
            st.session_state["jump_requested"] = True
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

            st.session_state["reset_frames"] = True
            st.rerun()
