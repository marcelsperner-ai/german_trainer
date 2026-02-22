import streamlit as st
import random
import re

def clean_grammar(text):
    """Removes grammatical hints in parentheses for a cleaner question display."""
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def render(row, df, next_fn):
    # The full target (e.g., "nach + D")
    correct_answer = str(row['Präposition']).strip()
    
    # If the data is empty or placeholder, skip
    if not correct_answer or correct_answer in ["–", ""]:
        st.warning("Keine Präpositions-Daten für diesen Eintrag vorhanden.")
        return

    # Initialize session state for this specific trainer to prevent shuffling on every click
    # and to track feedback
    if "prep_options" not in st.session_state or st.session_state.get("current_prep_idx") != st.session_state.idx:
        common_distractors = [
            "an + A", "an + D", "auf + A", "auf + D", "für + A", 
            "in + A", "in + D", "mit + D", "nach + D", "über + A", 
            "um + A", "von + D", "zu + D", "vor + D", "gegen + A", "bei + D"
        ]
        if correct_answer in common_distractors:
            common_distractors.remove(correct_answer)
        
        # Create and shuffle options once per vocabulary item
        opts = list(set([correct_answer] + random.sample(common_distractors, 3)))
        random.shuffle(opts)
        
        st.session_state.prep_options = opts
        st.session_state.current_prep_idx = st.session_state.idx
        st.session_state.prep_feedback = None

    # Display the expression as the prompt
    st.markdown(f"""<div class="vocab-card">
        <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">Ergänze die Präposition + Kasus:</div>
        <div class="main-word">{clean_grammar(row['Deutsch'])}</div>
        <div class="sub-word">{row['Farsi']}</div>
    </div>""", unsafe_allow_html=True)

    # Show persistent feedback if it exists
    if st.session_state.prep_feedback == "error":
        st.error("Leider nicht richtig. Versuche es noch einmal!")
    elif st.session_state.prep_feedback == "success":
        st.success(f"Richtig! **{clean_grammar(row['Deutsch'])} {correct_answer}**")
        
        # Show context/examples after correct answer
        example_de = str(row.get('Beispielsatz', '')).strip()
        example_fa = str(row.get('Beispielsatz_Farsi', '')).strip()
        
        if example_de or example_fa:
            st.markdown(f"""<div class="example-box">
                <b>Beispiel:</b><br>
                <span style="color: #1a1a1a;">{example_de}</span><br>
                <i style="color: #555;">{example_fa}</i>
            </div>""", unsafe_allow_html=True)

    # UI for the buttons (only if not already successful, or always show them)
    # We keep buttons visible so the user can try again
    cols = st.columns(2)
    for i, opt in enumerate(st.session_state.prep_options):
        if cols[i%2].button(opt, key=f"prep_opt_{opt}", use_container_width=True):
            if opt == correct_answer:
                st.session_state.prep_feedback = "success"
                st.rerun()
            else:
                st.session_state.prep_feedback = "error"
                st.rerun()