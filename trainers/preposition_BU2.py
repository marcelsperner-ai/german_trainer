import streamlit as st
import random
import re

def clean_grammar(text):
    """Entfernt grammatikalische Hinweise in Klammern für eine sauberere Anzeige."""
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def get_all_valid_preps(target_deutsch, df):
    """Durchsucht die gesamte CSV nach allen gültigen Präpositionen für einen deutschen Ausdruck."""
    all_valid = set()
    # Finde alle Zeilen, in denen der deutsche Begriff exakt übereinstimmt
    matches = df[df['Deutsch'] == target_deutsch]
    
    for val in matches['Präposition']:
        val_str = str(val).strip()
        if val_str and val_str not in ["–", ""]:
            # Trenne Einträge, die mit '/' in einer Zelle kombiniert sind
            parts = [p.strip() for p in val_str.split('/')]
            all_valid.update(parts)
    return sorted(list(all_valid)), matches

def render(row, df, next_fn):
    target_deutsch = row['Deutsch']
    
    # Extrahiere alle korrekten Präpositionen und alle zugehörigen Zeilen (für Beispielsätze)
    all_correct_preps, related_rows = get_all_valid_preps(target_deutsch, df)
    
    if not all_correct_preps:
        st.warning("Keine Präpositions-Daten für diesen Eintrag gefunden.")
        return

    # Status im session_state verwalten
    state_key = f"prep_multi_{st.session_state.idx}"
    if state_key not in st.session_state:
        # Distraktoren (falsche Optionen) auswählen
        common_distractors = [
            "an + A", "an + D", "auf + A", "auf + D", "für + A", 
            "in + A", "in + D", "mit + D", "nach + D", "über + A", 
            "um + A", "von + D", "zu + D", "vor + D", "gegen + A", "bei + D"
        ]
        distractors = [d for d in common_distractors if d not in all_correct_preps]
        
        # Richtige und falsche Optionen mischen
        num_distractors = max(4, len(all_correct_preps) + 2)
        random_distractors = random.sample(distractors, min(len(distractors), num_distractors - len(all_correct_preps)))
        
        options = list(set(all_correct_preps + random_distractors))
        random.shuffle(options)
        
        st.session_state[state_key] = {
            "options": options,
            "selected": set(),
            "finished": False
        }

    state = st.session_state[state_key]

    # Anzeige der Fragen-Karte
    st.markdown(f"""<div class="vocab-card">
        <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">
            Wähle alle zugehörigen Präpositionen ({len(all_correct_preps)} insgesamt):
        </div>
        <div class="main-word">{clean_grammar(target_deutsch)}</div>
        <div class="sub-word">{row['Farsi']}</div>
    </div>""", unsafe_allow_html=True)

    # Hinweis auf fehlende Einträge, wenn bereits etwas gefunden wurde, aber noch nicht alles
    if len(state["selected"]) > 0 and not state["finished"]:
        noch_zu_finden = len(all_correct_preps) - len(state["selected"])
        st.info(f"Gut! Du hast {len(state['selected'])} von {len(all_correct_preps)} gefunden. Es fehlen noch {noch_zu_finden}.")

    # Anzeige der Antwort-Buttons
    cols = st.columns(2)
    for i, opt in enumerate(state["options"]):
        is_selected = opt in state["selected"]
        is_correct = opt in all_correct_preps
        
        # Button-Stil basierend auf dem Auswahlstatus ändern
        button_type = "primary" if is_selected and is_correct else "secondary"
        
        if cols[i%2].button(opt, key=f"btn_{opt}_{st.session_state.idx}", use_container_width=True, type=button_type):
            if is_correct:
                state["selected"].add(opt)
                if len(state["selected"]) == len(all_correct_preps):
                    state["finished"] = True
                st.rerun()
            else:
                st.error(f"'{opt}' ist für diesen Ausdruck nicht korrekt.")

    # Ergebnisse und Beispiele nach Abschluss anzeigen
    if state["finished"]:
        st.success(f"Gut gemacht! Alle Einträge gefunden: **{', '.join(all_correct_preps)}**")
        
        st.markdown("### Beispielsätze:")
        for _, r in related_rows.iterrows():
            ex_de = str(r.get('Beispielsatz', '')).strip()
            ex_fa = str(r.get('Beispielsatz_Farsi', '')).strip()
            curr_prep = str(r.get('Präposition', ''))
            
            if ex_de:
                st.markdown(f"""<div class="example-box">
                    <small style="color: blue;">[{curr_prep}]</small><br>
                    <span style="color: #1a1a1a;">{ex_de}</span><br>
                    <i style="color: #555;">{ex_fa}</i>
                </div>""", unsafe_allow_html=True)