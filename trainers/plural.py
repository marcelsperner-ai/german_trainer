import streamlit as st

def render(row, df, next_fn, log_event):
    # Den Plural aus der aktuellen Zeile extrahieren
    target_plural = str(row.get('Plural', '')).strip()
    
    # WICHTIG: Wenn kein Plural vorhanden ist (leer oder "–"), 
    # wird dieser Ausdruck automatisch übersprungen.
    if not target_plural or target_plural in ["–", "", "-"]:
        next_fn()
        st.rerun()

    # Styling-Hilfsfunktion für die Kartenanzeige
    def card_display(main, sub, info=""):
        st.markdown(f"""<div class="vocab-card">
            <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">
                Wie lautet die Pluralform des Nomens in diesem Ausdruck?
            </div>
            <div class="main-word">{main}</div>
            <div class="sub-word">{sub}</div>
            <div style="font-size: 12px; color: gray; margin-top: 10px;">{info}</div>
        </div>""", unsafe_allow_html=True)

    # Das Wort auf der Vorderseite (der deutsche Ausdruck)
    front_content = str(row.get('Deutsch', '')).strip()
    farsi_hint = str(row.get('Farsi', '')).strip()

    # Karten-Logik (Flip-Card-Prinzip)
    if not st.session_state.get('show_solution', False):
        card_display(front_content, "???", f"Hinweis (Farsi): {farsi_hint}")
        if st.button("Plural zeigen", type="primary", use_container_width=True, key="plural_show"):
            st.session_state.show_solution = True
            st.rerun()
    else:
        # Lösung wird angezeigt
        card_display(target_plural, front_content, f"Bedeutung: {farsi_hint}")
        
        # Beispielsätze anzeigen, falls vorhanden
        example_de = str(row.get('Beispielsatz', '')).strip()
        example_fa = str(row.get('Beispielsatz_Farsi', '')).strip()
        
        if example_de or example_fa:
            st.markdown(f"""<div class="example-box">
                <b>Kontext:</b><br>
                <span style="color: #1a1a1a;">{example_de}</span><br>
                <i style="color: #555;">{example_fa}</i>
            </div>""", unsafe_allow_html=True)
            
        st.info("Nutze die Buttons unten für die Bewertung.")