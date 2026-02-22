import streamlit as st

def render(row, df, next_fn, log_event):
    if "art_direction" not in st.session_state:
        st.session_state.art_direction = "Deutsch -> Artikel"
    
    direction = st.radio(
        "Lernrichtung wählen:",
        ["Deutsch -> Artikel", "Farsi -> Artikel"],
        index=0 if st.session_state.art_direction == "Deutsch -> Artikel" else 1,
        horizontal=True,
        key=f"art_dir_toggle_{st.session_state.idx}"
    )
    st.session_state.art_direction = direction

    correct_article = str(row.get('Artikel', '')).strip().lower()
    if correct_article not in ["der", "die", "das"]:
        next_fn(); st.rerun()

    target_deutsch = str(row.get('Deutsch', '')).strip()
    q_text = target_deutsch if direction == "Deutsch -> Artikel" else row.get('Farsi', '')

    state_key = f"art_state_{st.session_state.idx}"
    if state_key not in st.session_state:
        st.session_state[state_key] = {"selected": None, "finished": False, "feedback": None}
    
    state = st.session_state[state_key]

    # Feedback-Anzeige
    if state["feedback"] == "incorrect":
        st.error("Das war leider der falsche Artikel. Versuche es noch einmal!")
    elif state["feedback"] == "correct":
        st.success(f"Richtig! Es heißt: **{correct_article} {target_deutsch}**")

    st.markdown(f"""<div class="vocab-card"><div class="main-word">{q_text}</div><div class="sub-word">{target_deutsch if direction == "Farsi -> Artikel" else ""}</div></div>""", unsafe_allow_html=True)

    articles = ["der", "die", "das"]
    cols = st.columns(3)
    
    for i, art in enumerate(articles):
        btn_type = "primary" if state["selected"] == art and art == correct_article else "secondary"
        if cols[i].button(art.capitalize(), key=f"btn_art_sel_{art}_{st.session_state.idx}", use_container_width=True, type=btn_type):
            state["selected"] = art
            if art == correct_article:
                state["feedback"] = "correct"
                state["finished"] = True
                st.session_state.show_solution = True
                log_event(st.session_state.current_vocab_key, "article", target_deutsch, "Correct")
            else:
                state["feedback"] = "incorrect"
                log_event(st.session_state.current_vocab_key, "article", target_deutsch, "Incorrect")
            st.rerun()