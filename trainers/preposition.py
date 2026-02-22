import streamlit as st
import random
import re

def clean_grammar(text):
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def get_all_valid_preps(target_deutsch, df):
    all_valid = set()
    matches = df[df['Deutsch'] == target_deutsch]
    for val in matches['Präposition']:
        val_str = str(val).strip()
        if val_str and val_str not in ["–", ""]:
            parts = [p.strip() for p in val_str.split('/')]
            all_valid.update(parts)
    return sorted(list(all_valid)), matches

def render(row, df, next_fn, log_event):
    if "prep_direction" not in st.session_state:
        st.session_state.prep_direction = "Farsi -> Deutsch"
    
    direction = st.radio(
        "Lernrichtung wählen:",
        ["Farsi -> Deutsch", "Deutsch -> Farsi"],
        index=0 if st.session_state.prep_direction == "Farsi -> Deutsch" else 1,
        horizontal=True,
        key=f"prep_dir_toggle_{st.session_state.idx}"
    )
    st.session_state.prep_direction = direction

    target_deutsch = row['Deutsch']
    all_correct_preps, related_rows = get_all_valid_preps(target_deutsch, df)
    
    if not all_correct_preps:
        st.warning("Keine Präpositions-Daten gefunden.")
        return

    # Status-Management
    state_key = f"prep_multi_{st.session_state.idx}"
    if state_key not in st.session_state:
        common = ["an + A", "an + D", "auf + A", "auf + D", "für + A", "in + A", "in + D", "mit + D", "nach + D", "über + A", "um + A", "von + D", "zu + D", "vor + D", "gegen + A", "bei + D"]
        distractors = [d for d in common if d not in all_correct_preps]
        opts = list(set(all_correct_preps + random.sample(distractors, 4)))
        random.shuffle(opts)
        st.session_state[state_key] = {
            "options": opts, 
            "selected": set(), 
            "finished": False,
            "feedback": None
        }

    state = st.session_state[state_key]
    
    # Feedback-Meldungen oben anzeigen
    if state["feedback"] == "incorrect":
        st.error("Leider nicht korrekt. Versuche es noch einmal!")
    elif state["finished"]:
        st.success(f"Gut gemacht! Alle gefunden: **{', '.join(all_correct_preps)}**")

    # Zählung der fehlenden Präpositionen
    if not state["finished"]:
        noch_zu_finden = len(all_correct_preps) - len(state["selected"])
        if len(state["selected"]) == 0:
            st.info(f"Finde alle passenden Präpositionen ({len(all_correct_preps)} insgesamt).")
        else:
            st.info(f"Gut! Du hast {len(state['selected'])} von {len(all_correct_preps)} gefunden. Es fehlen noch {noch_zu_finden}.")

    q_main = row['Farsi'] if direction == "Farsi -> Deutsch" else clean_grammar(target_deutsch)
    q_sub = clean_grammar(target_deutsch) if direction == "Farsi -> Deutsch" else row['Farsi']

    st.markdown(f"""<div class="vocab-card"><div class="main-word">{q_main}</div><div class="sub-word">{q_sub}</div></div>""", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, opt in enumerate(state["options"]):
        is_sel = opt in state["selected"]
        btn_type = "primary" if is_sel else "secondary"
        if cols[i%2].button(opt, key=f"btn_prep_opt_{opt}_{st.session_state.idx}", use_container_width=True, type=btn_type):
            if opt in all_correct_preps:
                state["feedback"] = "correct"
                if opt not in state["selected"]:
                    state["selected"].add(opt)
                    log_event(st.session_state.current_vocab_key, "preposition", target_deutsch, "Correct")
                if len(state["selected"]) == len(all_correct_preps): state["finished"] = True
                st.rerun()
            else:
                state["feedback"] = "incorrect"
                log_event(st.session_state.current_vocab_key, "preposition", target_deutsch, "Incorrect")
                st.rerun()

    if state["finished"]:
        st.markdown("### Beispielsätze:")
        for _, r in related_rows.iterrows():
            ex_de = str(r.get('Beispielsatz', '')).strip()
            if ex_de:
                st.markdown(f"""<div class="example-box">
                    <small style="color: blue;">[{r.get('Präposition', '')}]</small><br>
                    {ex_de}<br><i style="color: #555;">{r.get('Beispielsatz_Farsi', '')}</i>
                </div>""", unsafe_allow_html=True)