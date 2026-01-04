import streamlit as st
import pandas as pd
import random
import re
import os

# --- KONFIGURATION ---
st.set_page_config(page_title="Vokabeltrainer", layout="wide")

# --- DATEIEN DEFINITION ---
FILES = {
    "B2: Verben mit Präpositionen": "vokabeln.csv",
    "B1: Allgemeiner Wortschatz": "vokabeln_b1.csv",
    "B1: Teil 2 (Einkaufen & Service)": "vokabeln_b1_teil2.csv"
}

# --- DATEN MANAGEMENT ---

def load_data(filename):
    """Lädt Daten und bereinigt sie."""
    if not os.path.exists(filename):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filename, on_bad_lines='skip')
        
        # Standardspalten auffüllen
        required_cols = ['Deutsch', 'Farsi', 'English', 'Beispielsatz', 'Beispielsatz_Farsi', 'Status']
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" if col != 'Status' else "Neutral"
        
        # Spezialspalten für B2 (Präpositionen)
        if 'Präposition' not in df.columns:
            df['Präposition'] = ""
            
        # Spezialspalten für B1 (Artikel)
        if 'Artikel' not in df.columns:
            df['Artikel'] = ""
            
        return df.fillna("")
    except Exception as e:
        st.error(f"Fehler beim Laden von {filename}: {e}")
        return pd.DataFrame()

def save_data(df, filename):
    """Speichert den aktuellen Zustand."""
    df.to_csv(filename, index=False)

def update_status(df, index, status, filename):
    """Setzt den Status und speichert."""
    df.at[index, 'Status'] = status
    save_data(df, filename)
    st.toast(f"Status gespeichert: {status}", icon="💾")

def get_weighted_random_index(df):
    """Zufallsauswahl basierend auf Status."""
    if df.empty: return 0
    weights = [10 if s == 'Red' else 0.2 if s == 'Green' else 2 for s in df['Status']]
    return random.choices(df.index, weights=weights, k=1)[0]

def hide_term_in_sentence(sentence, term):
    """Versteckt den gesuchten Begriff im Satz."""
    if not sentence or not term: return sentence
    # Einfaches Ersetzen (Case Insensitive)
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub("___", sentence)

# --- UI LOGIK ---

st.title("🇩🇪 🇮🇷 Deutsch-Farsi Vokabeltrainer")

# 1. AUSWAHL DES LERN-SETS
dataset_name = st.sidebar.selectbox("Wähle dein Lern-Modul:", list(FILES.keys()))
current_file = FILES[dataset_name]

# Daten laden
if 'current_dataset' not in st.session_state or st.session_state.current_dataset != dataset_name:
    st.session_state.vocab_df = load_data(current_file)
    st.session_state.current_dataset = dataset_name
    st.session_state.history = []
    # Initialer Index
    if not st.session_state.vocab_df.empty:
        st.session_state.current_idx = get_weighted_random_index(st.session_state.vocab_df)
    else:
        st.session_state.current_idx = 0
    st.session_state.show_solution = False

df = st.session_state.vocab_df

# Check ob Daten da sind
if df.empty:
    st.info(f"Bitte lade die Datei '{current_file}' hoch oder erstelle sie.")
    st.stop()

# Helper für Navigation
def next_card():
    st.session_state.history.append(st.session_state.current_idx)
    st.session_state.current_idx = get_weighted_random_index(df)
    st.session_state.show_solution = False

def prev_card():
    if st.session_state.history:
        st.session_state.current_idx = st.session_state.history.pop()
        st.session_state.show_solution = False

# Aktuelle Zeile
row = df.iloc[st.session_state.current_idx]
is_b2_mode = "B2" in dataset_name # Prüfen ob wir im B2 Modus sind (Präpositionen)

# --- UI TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🃏 Flashcards", "✍️ Schreiben", "🧩 Lückentext", "📝 Liste"])

# --- TAB 1: FLASHCARDS ---
with tab1:
    st.subheader("Wissenstest")
    c1, c2 = st.columns(2)
    
    with c1:
        st.info(f"**{row['Deutsch']}**")
        if not is_b2_mode and row['Plural']:
             st.caption(f"Plural: {row['Plural']}")
    
    with c2:
        if st.session_state.show_solution:
            # Lösung anzeigen
            if is_b2_mode:
                st.success(f"Präposition: **{row['Präposition']}**")
            else:
                if row['Artikel']:
                    st.success(f"Artikel: **{row['Artikel']}**")
                else:
                    st.success("Kein Artikel (Verb/Adjektiv)")
            
            st.markdown(f"### 🇮🇷 {row['Farsi']}")
            st.markdown("---")
            st.markdown(f"🇩🇪 _{row['Beispielsatz']}_")
            if row['Beispielsatz_Farsi']:
                st.markdown(f"🇮🇷 _{row['Beispielsatz_Farsi']}_")
                
            # Bewertung
            st.write("Wie war's?")
            col_a, col_b = st.columns(2)
            if col_a.button("🔴 Schwer", key="fc_red"):
                update_status(df, st.session_state.current_idx, "Red", current_file)
                st.rerun()
            if col_b.button("🟢 Einfach", key="fc_green"):
                update_status(df, st.session_state.current_idx, "Green", current_file)
                st.rerun()

        else:
            st.markdown("### ???")
            question_text = "Welche Präposition?" if is_b2_mode else "Welcher Artikel?"
            st.write(question_text)
            if st.button("Lösung zeigen", key="fc_sol"):
                st.session_state.show_solution = True
                st.rerun()

    st.markdown("---")
    c_prev, c_next = st.columns([1,1])
    if c_prev.button("⬅️ Zurück", key="fc_back", disabled=not st.session_state.history):
        prev_card()
        st.rerun()
    if c_next.button("Nächste Karte ➡️", key="fc_next", type="primary"):
        next_card()
        st.rerun()

# --- TAB 2: SCHREIBEN ---
with tab2:
    st.subheader("Übersetze ins Deutsche")
    st.markdown(f"### 🇮🇷 {row['Farsi']}")
    
    with st.form("write_form"):
        inp = st.text_input("Deutsches Wort:")
        submitted = st.form_submit_button("Prüfen")
        
    if submitted:
        st.session_state.show_solution = True
        
    if st.session_state.show_solution:
        if inp.lower().strip() in row['Deutsch'].lower():
            st.success("Richtig!")
        else:
            st.error(f"Leider falsch. Lösung: **{row['Deutsch']}**")
            
        st.markdown(f"🇩🇪 _{row['Beispielsatz']}_")
        
        # Bewertung (JETZT AUCH HIER)
        st.write("Bewertung:")
        col_a, col_b = st.columns(2)
        if col_a.button("🔴 Schwer", key="wr_red"):
            update_status(df, st.session_state.current_idx, "Red", current_file)
            st.rerun()
        if col_b.button("🟢 Einfach", key="wr_green"):
            update_status(df, st.session_state.current_idx, "Green", current_file)
            st.rerun()

    st.markdown("---")
    
    # Navigation (JETZT MIT BACK BUTTON)
    c_prev, c_next = st.columns([1,1])
    if c_prev.button("⬅️ Zurück", key="wr_back", disabled=not st.session_state.history):
        prev_card()
        st.rerun()
    if c_next.button("Nächste Karte ➡️", key="wr_next", type="primary"):
        next_card()
        st.rerun()

# --- TAB 3: LÜCKENTEXT ---
with tab3:
    st.subheader("Ergänze")
    
    # Was verstecken wir? B2 -> Präposition, B1 -> Das Wort selbst
    hidden_text = row['Beispielsatz']
    term_to_hide = row['Präposition'].split('+')[0].split('/')[0].strip() if is_b2_mode else row['Deutsch']
    
    masked_sentence = hide_term_in_sentence(hidden_text, term_to_hide)
    
    st.markdown(f"### {masked_sentence}")
    st.caption(f"Hinweis: {row['Farsi']}")
    
    if st.button("Aufdecken", key="gap_sol"):
        st.session_state.show_solution = True
        st.rerun()
        
    if st.session_state.show_solution:
        st.success(f"Lösung: **{term_to_hide}**")
        st.markdown(f"_{row['Beispielsatz']}_")
        
        # Bewertung (JETZT AUCH HIER)
        st.write("Bewertung:")
        col_a, col_b = st.columns(2)
        if col_a.button("🔴 Schwer", key="gap_red"):
            update_status(df, st.session_state.current_idx, "Red", current_file)
            st.rerun()
        if col_b.button("🟢 Einfach", key="gap_green"):
            update_status(df, st.session_state.current_idx, "Green", current_file)
            st.rerun()
        
    st.markdown("---")
    
    # Navigation (JETZT MIT BACK BUTTON)
    c_prev, c_next = st.columns([1,1])
    if c_prev.button("⬅️ Zurück", key="gap_back", disabled=not st.session_state.history):
        prev_card()
        st.rerun()
    if c_next.button("Nächste Karte ➡️", key="gap_next", type="primary"):
        next_card()
        st.rerun()

# --- TAB 4: LISTE ---
with tab4:
    st.subheader("Vokabelliste bearbeiten")
    edited_df = st.data_editor(df, num_rows="dynamic", key="editor")
    if st.button("💾 Speichern"):
        st.session_state.vocab_df = edited_df
        save_data(edited_df, current_file)
        st.success("Gespeichert!")