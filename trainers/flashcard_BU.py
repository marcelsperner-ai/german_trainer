import streamlit as st

def render(row, df, next_fn):
    # Styling-Hilfsfunktion
    def card_display(main, sub, info=""):
        st.markdown(f"""<div class="vocab-card">
            <div class="main-word">{main}</div>
            <div class="sub-word">{sub}</div>
            <div style="font-size: 12px; color: gray; margin-top: 10px;">{info}</div>
        </div>""", unsafe_allow_html=True)

    # Auswahl der Lernrichtung (merkt sich die Einstellung in der Session)
    if "flashcard_direction" not in st.session_state:
        st.session_state.flashcard_direction = "Farsi -> Deutsch"
    
    # Richtungswahl über dem UI
    direction = st.radio(
        "Lernrichtung wählen:",
        ["Farsi -> Deutsch", "Deutsch -> Farsi"],
        index=0 if st.session_state.flashcard_direction == "Farsi -> Deutsch" else 1,
        horizontal=True,
        key="direction_toggle"
    )
    st.session_state.flashcard_direction = direction

    # Logik für die Anzeige basierend auf der Richtung
    if direction == "Farsi -> Deutsch":
        front_word = row['Farsi']
        back_word = row['Deutsch']
        instruction = "Wie lautet der deutsche Ausdruck?"
    else:
        front_word = row['Deutsch']
        back_word = row['Farsi']
        instruction = "Was bedeutet das auf Farsi?"

    # Karten-Logik
    if not st.session_state.get('show_solution', False):
        card_display(front_word, "???", instruction)
        if st.button("Lösung zeigen", type="primary", use_container_width=True):
            st.session_state.show_solution = True
            st.rerun()
    else:
        # Lösung wird angezeigt
        card_display(back_word, front_word)
        
        # Beispielsätze anzeigen, falls vorhanden
        example_de = str(row.get('Beispielsatz', '')).strip()
        example_fa = str(row.get('Beispielsatz_Farsi', '')).strip()
        
        if example_de or example_fa:
            st.markdown(f"""<div class="example-box">
                <b>Beispiel:</b><br>
                <span style="color: #1a1a1a;">{example_de}</span><br>
                <i style="color: #555;">{example_fa}</i>
            </div>""", unsafe_allow_html=True)
            
        st.info("Nutze die Buttons unten, um diese Vokabel zu bewerten.")