import streamlit as st
import random

def render(row, df, next_fn, log_event):
    # Eindeutiger Key für dieses Wort
    state_key = f"rel_sent_state_{st.session_state.idx}"
    
    if state_key not in st.session_state:
        # Satzbau-Optionen vorbereiten
        correct_s = str(row.get('Satz_Korrekt', '')).strip()
        wrong_s = str(row.get('Satz_Falsch', '')).strip()
        all_options = [correct_s, wrong_s]
        random.shuffle(all_options)
        
        st.session_state[state_key] = {
            "options": all_options,
            "solved": False,
            "feedback": None
        }

    state = st.session_state[state_key]

    st.markdown(f"""<div class="vocab-card">
        <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">Welche Satzstellung ist korrekt?</div>
        <div class="main-word" style="font-size: 18px !important;">{row.get('Farsi', '')}</div>
        <div class="sub-word">Achte auf das Verb am Ende des Relativsatzes!</div>
    </div>""", unsafe_allow_html=True)

    if state["feedback"] == "incorrect":
        st.error("Falscher Satzbau! Im Relativsatz steht das konjugierte Verb ganz am Ende.")
    elif state["solved"]:
        st.success("Sehr gut! Der Satzbau ist korrekt.")
        st.session_state.show_solution = True

    # Antwort-Buttons (Ganze Sätze)
    for i, opt in enumerate(state["options"]):
        is_correct = (opt == row['Satz_Korrekt'])
        btn_type = "primary" if state["solved"] and is_correct else "secondary"
        
        if st.button(opt, key=f"btn_rels_{i}_{st.session_state.idx}", use_container_width=True, type=btn_type):
            if is_correct:
                state["solved"] = True
                state["feedback"] = "correct"
                log_event(st.session_state.current_vocab_key, "rel_sentence", opt[:30], "Correct")
            else:
                state["feedback"] = "incorrect"
                log_event(st.session_state.current_vocab_key, "rel_sentence", opt[:30], "Incorrect")
            st.rerun()