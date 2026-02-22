import streamlit as st
import random

def render(row, df, next_fn, log_event):
    # Initialisierung des Session-States für das Feedback
    state_key = f"rel_state_{st.session_state.idx}"
    if state_key not in st.session_state:
        # Pronomen-Optionen vorbereiten
        correct_p = str(row.get('Relativpronomen', '')).strip()
        distractors = [d.strip() for d in str(row.get('Distraktoren', '')).split(',') if d.strip()]
        all_options = list(set([correct_p] + distractors))
        random.shuffle(all_options)
        
        # Satzbau-Optionen vorbereiten
        correct_s = str(row.get('Satz_Korrekt', '')).strip()
        wrong_s = str(row.get('Satz_Falsch', '')).strip()
        sentence_options = [correct_s, wrong_s]
        random.shuffle(sentence_options)
        
        st.session_state[state_key] = {
            "p_options": all_options,
            "s_options": sentence_options,
            "p_solved": False,
            "s_solved": False,
            "feedback_p": None,
            "feedback_s": None
        }

    state = st.session_state[state_key]

    # --- TEIL 1: Pronomen Quiz ---
    st.markdown("### 1. Das richtige Relativpronomen")
    st.markdown(f"""<div class="vocab-card">
        <div class="main-word">{str(row['Deutsch']).replace('___', ' <span style="color:red;">?</span> ')}</div>
        <div class="sub-word">{row.get('Farsi', '')}</div>
        <div style="font-size: 12px; color: gray; margin-top: 10px;">Hinweis: {row.get('Hinweis', 'Kein Hinweis')}</div>
    </div>""", unsafe_allow_html=True)

    if state["feedback_p"] == "incorrect":
        st.error("Das Pronomen ist leider falsch.")
    elif state["p_solved"]:
        st.success(f"Richtig! Das Pronomen ist: **{row['Relativpronomen']}**")

    cols = st.columns(len(state["p_options"]))
    for i, opt in enumerate(state["p_options"]):
        is_correct = (opt == row['Relativpronomen'])
        btn_type = "primary" if state["p_solved"] and is_correct else "secondary"
        
        if cols[i].button(opt, key=f"p_opt_{opt}_{st.session_state.idx}", use_container_width=True, type=btn_type):
            if is_correct:
                state["p_solved"] = True
                state["feedback_p"] = "correct"
                log_event(st.session_state.current_vocab_key, "relative_quiz", row.get('Deutsch', 'Gap'), "Correct")
            else:
                state["feedback_p"] = "incorrect"
                log_event(st.session_state.current_vocab_key, "relative_quiz", row.get('Deutsch', 'Gap'), "Incorrect")
            st.rerun()

    # --- TEIL 2: Satzbau Quiz (nur wenn Pronomen gelöst) ---
    if state["p_solved"] and row.get('Satz_Korrekt'):
        st.divider()
        st.markdown("### 2. Der korrekte Satzbau")
        st.write("Welcher Satz ist grammatikalisch richtig?")
        
        if state["feedback_s"] == "incorrect":
            st.error("Achte auf die Position des Verbs!")
        elif state["s_solved"]:
            st.success("Perfekt! Der Satzbau stimmt.")
            st.session_state.show_solution = True # Aktiviert die Bewertung unten

        for s_opt in state["s_options"]:
            is_correct_s = (s_opt == row['Satz_Korrekt'])
            s_btn_type = "primary" if state["s_solved"] and is_correct_s else "secondary"
            
            if st.button(s_opt, key=f"s_opt_{hash(s_opt)}_{st.session_state.idx}", use_container_width=True, type=s_btn_type):
                if is_correct_s:
                    state["s_solved"] = True
                    state["feedback_s"] = "correct"
                    log_event(st.session_state.current_vocab_key, "relative_sentence", s_opt[:20], "Correct")
                else:
                    state["feedback_s"] = "incorrect"
                    log_event(st.session_state.current_vocab_key, "relative_sentence", s_opt[:20], "Incorrect")
                st.rerun()