import streamlit as st
import re

def clean_grammar(text):
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def render(row, df, next_fn, log_event):
    if "flashcard_direction" not in st.session_state:
        st.session_state.flashcard_direction = "Farsi -> Deutsch"
    
    direction = st.radio(
        "Lernrichtung wählen:",
        ["Farsi -> Deutsch", "Deutsch -> Farsi"],
        index=0 if st.session_state.flashcard_direction == "Farsi -> Deutsch" else 1,
        horizontal=True,
        key=f"flash_dir_toggle_{st.session_state.idx}"
    )
    st.session_state.flashcard_direction = direction

    if direction == "Farsi -> Deutsch":
        front_word = str(row['Farsi']).strip()
        back_word = str(row['Deutsch']).strip()
        instruction = "Wie lautet der deutsche Ausdruck?"
    else:
        front_word = clean_grammar(str(row['Deutsch']))
        back_word = str(row['Farsi']).strip()
        instruction = "Was bedeutet das auf Farsi?"

    if not st.session_state.get('show_solution', False):
        st.markdown(f"""<div class="vocab-card"><div class="main-word">{front_word}</div><div class="sub-word">???</div><div style="font-size: 12px; color: gray; margin-top: 10px;">{instruction}</div></div>""", unsafe_allow_html=True)
        if st.button("Lösung zeigen", type="primary", use_container_width=True, key=f"flash_btn_sol_{st.session_state.idx}"):
            st.session_state.show_solution = True
            st.rerun()
    else:
        st.markdown(f"""<div class="vocab-card"><div class="main-word">{back_word}</div><div class="sub-word">{front_word}</div></div>""", unsafe_allow_html=True)
        
        grammatik = []
        for col in ['Artikel', 'Plural', 'Perfekt', 'Präteritum']:
            val = str(row.get(col, '')).strip()
            if val and val not in ["-", "–"]:
                grammatik.append(f"<b>{col}:</b> {val}")
        
        if grammatik:
            st.markdown(f"""<div style="background-color: #f0f2f6; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-size: 14px;">{" | ".join(grammatik)}</div>""", unsafe_allow_html=True)

        example_de = str(row.get('Beispielsatz', '')).strip()
        if example_de:
            st.markdown(f"""<div class="example-box"><b>Beispiel:</b><br>{example_de}</div>""", unsafe_allow_html=True)