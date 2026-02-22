import streamlit as st

def render(row, df, next_fn):
    # Den Artikel aus der aktuellen Zeile extrahieren
    correct_article = str(row.get('Artikel', '')).strip().lower()
    valid_articles = ["der", "die", "das"]

    # WICHTIG: Wenn der Artikel ungültig ist (nicht der, die, das), 
    # wird dieser Ausdruck automatisch übersprungen.
    if correct_article not in valid_articles:
        next_fn()
        st.rerun()

    # Das Ziel-Wort für den Artikel-Check (meistens das Nomen in der Wendung)
    target_phrase = str(row.get('Deutsch', '')).strip()

    # Styling-Hilfsfunktion
    def card_display(main, sub, info=""):
        st.markdown(f"""<div class="vocab-card">
            <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">
                Welcher Artikel gehört zu dem Nomen in diesem Ausdruck?
            </div>
            <div class="main-word">{main}</div>
            <div class="sub-word">{sub}</div>
            <div style="font-size: 12px; color: gray; margin-top: 10px;">{info}</div>
        </div>""", unsafe_allow_html=True)

    # Initialisierung des Session-Status für dieses Modul
    state_key = f"article_check_{st.session_state.idx}"
    if state_key not in st.session_state:
        st.session_state[state_key] = {
            "selected": None,
            "finished": False
        }
    
    state = st.session_state[state_key]

    # Anzeige der Frage
    card_display(target_phrase, row.get('Farsi', ''))

    # Auswahl-Buttons
    articles = ["der", "die", "das"]
    cols = st.columns(3)
    
    for i, art in enumerate(articles):
        # Bestimme Button-Typ basierend auf Auswahl
        button_type = "secondary"
        if state["selected"] == art:
            if art == correct_article:
                button_type = "primary" # Highlight für die richtige Antwort
        
        if cols[i].button(art.capitalize(), key=f"art_{art}_{st.session_state.idx}", use_container_width=True, type=button_type):
            state["selected"] = art
            if art == correct_article:
                state["finished"] = True
                st.session_state.show_solution = True # Aktiviert die globalen Bewertungs-Buttons in app.py
            st.rerun()

    # Feedback-Anzeige
    if state["selected"]:
        if state["selected"] == correct_article:
            st.success(f"Richtig! Es heißt: **{correct_article}** ({target_phrase})")
            
            # Beispiele einblenden falls vorhanden
            example_de = str(row.get('Beispielsatz', '')).strip()
            example_fa = str(row.get('Beispielsatz_Farsi', '')).strip()
            
            if example_de or example_fa:
                st.markdown(f"""<div class="example-box">
                    <b>Beispiel:</b><br>
                    <span style="color: #1a1a1a;">{example_de}</span><br>
                    <i style="color: #555;">{example_fa}</i>
                </div>""", unsafe_allow_html=True)
        else:
            st.error(f"Leider falsch! Versuche es noch einmal.")