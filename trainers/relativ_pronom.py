import streamlit as st
import random

def render(row, df, next_fn, log_event):
    # Eindeutiger Key für dieses Wort
    state_key = f"rel_pron_state_{st.session_state.idx}"
    
    if state_key not in st.session_state:
        # Lösung und Distraktoren vorbereiten
        correct_p = str(row.get('Relativpronomen', '')).strip()
        dist_str = str(row.get('Distraktoren', ''))
        distractors = [d.strip() for d in dist_str.split(',') if d.strip()]
        
        all_options = list(set([correct_p] + distractors))
        random.shuffle(all_options)
        
        st.session_state[state_key] = {
            "options": all_options,
            "solved": False,
            "feedback": None
        }

    state = st.session_state[state_key]

    # UI Anzeige
    display_text = str(row['Deutsch']).replace('___', '<span style="color:red; font-weight:bold;"> [ ? ] </span>')
    
    st.markdown(f"""<div class="vocab-card">
        <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">Wähle das korrekte Relativpronomen:</div>
        <div class="main-word">{display_text}</div>
        <div class="sub-word">{row.get('Farsi', '')}</div>
        <div style="font-size: 13px; color: #666; margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;">
            <b>Hinweis:</b> {row.get('Hinweis', 'Kein Hinweis')}
        </div>
    </div>""", unsafe_allow_html=True)

    if state["feedback"] == "incorrect":
        st.error("Das Pronomen ist leider falsch. Prüfe Genus und Kasus!")
    elif state["solved"]:
        st.success(f"Richtig! Lösung: **{row['Relativpronomen']}**")
        st.session_state.show_solution = True

    # Antwort-Buttons
    cols = st.columns(len(state["options"]))
    for i, opt in enumerate(state["options"]):
        is_correct = (opt == row['Relativpronomen'])
        btn_type = "primary" if state["solved"] and is_correct else "secondary"
        
        if cols[i].button(opt, key=f"btn_relp_{opt}_{st.session_state.idx}", use_container_width=True, type=btn_type):
            if is_correct:
                state["solved"] = True
                state["feedback"] = "correct"
                log_event(st.session_state.current_vocab_key, "rel_pronoun", row['Deutsch'][:30], "Correct")
            else:
                state["feedback"] = "incorrect"
                log_event(st.session_state.current_vocab_key, "rel_pronoun", row['Deutsch'][:30], "Incorrect")
            st.rerun()