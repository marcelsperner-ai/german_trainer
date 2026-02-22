import streamlit as st

def render(row, df, next_fn, log_event):
    # Styling-Hilfsfunktion für die Kartenanzeige
    def card_display(main, sub, info=""):
        st.markdown(f"""<div class="vocab-card">
            <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">Wie lautet der passende Ausdruck?</div>
            <div class="main-word">{main}</div>
            <div class="sub-word">{sub}</div>
            <div style="font-size: 12px; color: gray; margin-top: 10px;">{info}</div>
        </div>""", unsafe_allow_html=True)

    # Das Wort auf der Vorderseite ist die Erläuterung (Synonym/Umschreibung)
    front_content = str(row.get('Erläuterung', 'Keine Erläuterung vorhanden')).strip()
    # Das gesuchte Wort ist der deutsche Ausdruck
    target_word = str(row.get('Deutsch', '')).strip()
    # Farsi als zusätzliche Gedankenstütze
    farsi_hint = str(row.get('Farsi', '')).strip()

    # Logik für das Aufdecken der Lösung
    if not st.session_state.get('show_solution', False):
        card_display(front_content, "???", f"Hinweis (Farsi): {farsi_hint}")
        if st.button("Lösung zeigen", type="primary", use_container_width=True, key="syn_show"):
            st.session_state.show_solution = True
            st.rerun()
    else:
        # Lösung wird angezeigt
        card_display(target_word, front_content, f"Bedeutung: {farsi_hint}")
        
        # Beispielsätze zur Festigung anzeigen
        example_de = str(row.get('Beispielsatz', '')).strip()
        example_fa = str(row.get('Beispielsatz_Farsi', '')).strip()
        
        if example_de or example_fa:
            st.markdown(f"""<div class="example-box">
                <b>Anwendungsbeispiel:</b><br>
                <span style="color: #1a1a1a;">{example_de}</span><br>
                <i style="color: #555;">{example_fa}</i>
            </div>""", unsafe_allow_html=True)
            
        st.info("Bewerte den Schwierigkeitsgrad unten, um fortzufahren.")