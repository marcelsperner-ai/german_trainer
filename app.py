import streamlit as st
import pandas as pd
import random
import re
import os
import json

# --- KONFIGURATION ---
st.set_page_config(page_title="Vokabeltrainer V2", layout="wide")
CONFIG_FILE = "modules.json"

# --- DATEN MANAGEMENT ---

def load_module_config():
    """Lädt die Liste der verfügbaren Module."""
    if not os.path.exists(CONFIG_FILE):
        # Fallback, falls JSON fehlt: Standard erstellen
        default_config = {"Start-Modul": "vokabeln.csv"}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_module_config(config):
    """Speichert die Liste der Module."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def create_new_module_file(filename):
    """Erstellt eine leere CSV mit allen nötigen Spalten."""
    columns = [
        'Deutsch', 'Farsi', 'English', 
        'Beispielsatz', 'Beispielsatz_Farsi', 
        'Status', 'Präposition', 'Artikel', 'Plural'
    ]
    df = pd.DataFrame(columns=columns)
    df.to_csv(filename, index=False)

def load_data(filename):
    if not os.path.exists(filename):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filename, on_bad_lines='skip')
        # Sicherstellen, dass alle Spalten existieren
        required_cols = ['Deutsch', 'Farsi', 'English', 'Beispielsatz', 'Beispielsatz_Farsi', 'Status', 'Präposition', 'Artikel', 'Plural']
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" if col != 'Status' else "Neutral"
        return df.fillna("")
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

def update_status(df, index, status, filename):
    df.at[index, 'Status'] = status
    save_data(df, filename)
    st.toast(f"Status gespeichert: {status}", icon="💾")

def get_weighted_random_index(df):
    if df.empty: return 0
    weights = [10 if s == 'Red' else 0.2 if s == 'Green' else 2 for s in df['Status']]
    # Fallback falls alle Gewichte 0 sind oder Fehler auftreten
    try:
        return random.choices(df.index, weights=weights, k=1)[0]
    except:
        return 0

def hide_term_in_sentence(sentence, term):
    if not sentence or not term: return sentence
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub("___", sentence)

# --- INITIALISIERUNG ---

# Module laden
modules = load_module_config()

# Session State für das aktive Modul
if 'current_dataset_name' not in st.session_state:
    # Erstes Modul als Standard
    first_key = list(modules.keys())[0] if modules else None
    st.session_state.current_dataset_name = first_key

# Aktueller Dateiname basierend auf Auswahl
current_file = modules.get(st.session_state.current_dataset_name, "vokabeln.csv")

# Daten laden (nur wenn sich das Modul ändert oder noch nichts da ist)
if 'vocab_df' not in st.session_state or st.session_state.get('loaded_file') != current_file:
    st.session_state.vocab_df = load_data(current_file)
    st.session_state.loaded_file = current_file
    st.session_state.history = []
    # Index reset
    if not st.session_state.vocab_df.empty:
        st.session_state.current_idx = get_weighted_random_index(st.session_state.vocab_df)
    else:
        st.session_state.current_idx = 0
    st.session_state.show_solution = False

df = st.session_state.vocab_df

# Navigation Helper
def next_card():
    st.session_state.history.append(st.session_state.current_idx)
    # Neu laden falls DF sich geändert hat (durch Editor)
    current_df = st.session_state.vocab_df
    if not current_df.empty:
        st.session_state.current_idx = get_weighted_random_index(current_df)
    st.session_state.show_solution = False

def prev_card():
    if st.session_state.history:
        st.session_state.current_idx = st.session_state.history.pop()
        st.session_state.show_solution = False

# --- SIDEBAR (DAS NEUE MENU) ---

with st.sidebar:
    st.title("📚 Module")
    
    # 1. Modul-Liste als Buttons
    st.caption("Wähle ein Thema:")
    for mod_name, mod_file in modules.items():
        # Button Styling: Primärfarbe für das aktive Modul
        btn_type = "primary" if st.session_state.current_dataset_name == mod_name else "secondary"
        
        if st.button(mod_name, key=f"btn_{mod_name}", type=btn_type, use_container_width=True):
            st.session_state.current_dataset_name = mod_name
            st.rerun() # App neu laden mit neuem Modul

    st.markdown("---")
    
    # 2. Neues Modul erstellen
    with st.expander("➕ Neues Modul erstellen"):
        with st.form("new_module_form"):
            new_mod_name = st.text_input("Name (z.B. 'Meine Vokabeln')")
            submit_new = st.form_submit_button("Erstellen")
            
            if submit_new and new_mod_name:
                if new_mod_name in modules:
                    st.error("Name existiert schon!")
                else:
                    # Dateinamen generieren (alles klein, keine Sonderzeichen)
                    safe_filename = "".join([c for c in new_mod_name if c.isalnum()]).lower() + "_custom.csv"
                    
                    # Datei erstellen
                    create_new_module_file(safe_filename)
                    
                    # In Config eintragen
                    modules[new_mod_name] = safe_filename
                    save_module_config(modules)
                    
                    # Direkt dahin wechseln
                    st.session_state.current_dataset_name = new_mod_name
                    st.success("Erstellt!")
                    st.rerun()

# --- HAUPTBEREICH ---

st.title(f"Lektion: {st.session_state.current_dataset_name}")

# Prüfen ob Daten da sind (leere neue Module abfangen)
if df.empty:
    st.info("Dieses Modul ist noch leer. Gehe zum Tab '📝 Liste & Bearbeiten', um Vokabeln hinzuzufügen!")
    # Dummy Row für Editor, damit er nicht abstürzt
    row = pd.Series({c: "" for c in df.columns})
    is_empty_mode = True
else:
    # Prüfen ob Index gültig (falls Zeilen gelöscht wurden)
    if st.session_state.current_idx not in df.index:
        st.session_state.current_idx = df.index[0]
    
    row = df.loc[st.session_state.current_idx]
    is_empty_mode = False

# Modus-Erkennung (Hat das Wort eine Präposition oder einen Artikel?)
is_b2_mode = "Präposition" in row and str(row['Präposition']).strip() != ""

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🃏 Flashcards", "✍️ Schreiben", "🧩 Lückentext", "📝 Liste & Bearbeiten"])

# --- TAB 1: FLASHCARDS ---
with tab1:
    if is_empty_mode:
        st.write("Bitte erst Vokabeln eintragen.")
    else:
        st.subheader("Wissenstest")
        c1, c2 = st.columns(2)
        
        with c1:
            st.info(f"**{row['Deutsch']}**")
            if not is_b2_mode and row['Plural']:
                 st.caption(f"Plural: {row['Plural']}")
        
        with c2:
            if st.session_state.show_solution:
                # Lösung
                if is_b2_mode:
                    st.success(f"Präposition: **{row['Präposition']}**")
                else:
                    art = row['Artikel'] if row['Artikel'] else "-"
                    st.success(f"Artikel: **{art}**")
                
                st.markdown(f"### 🇮🇷 {row['Farsi']}")
                if row['Beispielsatz']:
                    st.markdown("---")
                    st.markdown(f"🇩🇪 _{row['Beispielsatz']}_")
                if row['Beispielsatz_Farsi']:
                    st.markdown(f"🇮🇷 _{row['Beispielsatz_Farsi']}_")
                    
                # Bewertung
                st.write("Bewertung:")
                col_a, col_b = st.columns(2)
                if col_a.button("🔴 Schwer", key="fc_red"):
                    update_status(df, st.session_state.current_idx, "Red", current_file)
                    st.rerun()
                if col_b.button("🟢 Einfach", key="fc_green"):
                    update_status(df, st.session_state.current_idx, "Green", current_file)
                    st.rerun()

            else:
                st.markdown("### ???")
                q = "Welche Präposition?" if is_b2_mode else "Welcher Artikel / Bedeutung?"
                st.write(q)
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
    if is_empty_mode:
        st.write("Bitte erst Vokabeln eintragen.")
    else:
        st.subheader("Übersetze ins Deutsche")
        st.markdown(f"### 🇮🇷 {row['Farsi']}")
        
        with st.form("write_form"):
            inp = st.text_input("Deutsches Wort:")
            submitted = st.form_submit_button("Prüfen")
            
        if submitted:
            st.session_state.show_solution = True
            
        if st.session_state.show_solution:
            if inp.lower().strip() in str(row['Deutsch']).lower():
                st.success("Richtig!")
            else:
                st.error(f"Leider falsch. Lösung: **{row['Deutsch']}**")
                
            st.markdown(f"🇩🇪 _{row['Beispielsatz']}_")
            
            st.write("Bewertung:")
            col_a, col_b = st.columns(2)
            if col_a.button("🔴 Schwer", key="wr_red"):
                update_status(df, st.session_state.current_idx, "Red", current_file)
                st.rerun()
            if col_b.button("🟢 Einfach", key="wr_green"):
                update_status(df, st.session_state.current_idx, "Green", current_file)
                st.rerun()

        st.markdown("---")
        c_prev, c_next = st.columns([1,1])
        if c_prev.button("⬅️ Zurück", key="wr_back", disabled=not st.session_state.history):
            prev_card()
            st.rerun()
        if c_next.button("Nächste Karte ➡️", key="wr_next", type="primary"):
            next_card()
            st.rerun()

# --- TAB 3: LÜCKENTEXT ---
with tab3:
    if is_empty_mode or not row['Beispielsatz']:
        st.write("Keine Beispielsätze verfügbar.")
    else:
        st.subheader("Ergänze")
        
        # Was verstecken wir?
        hidden_text = row['Beispielsatz']
        if is_b2_mode:
            # Präposition extrahieren (alles vor dem +)
            term_to_hide = str(row['Präposition']).split('+')[0].split('/')[0].strip()
        else:
            term_to_hide = str(row['Deutsch'])
        
        masked_sentence = hide_term_in_sentence(hidden_text, term_to_hide)
        
        st.markdown(f"### {masked_sentence}")
        st.caption(f"Hinweis: {row['Farsi']}")
        
        if st.button("Aufdecken", key="gap_sol"):
            st.session_state.show_solution = True
            st.rerun()
            
        if st.session_state.show_solution:
            st.success(f"Lösung: **{term_to_hide}**")
            st.markdown(f"_{row['Beispielsatz']}_")
            
            st.write("Bewertung:")
            col_a, col_b = st.columns(2)
            if col_a.button("🔴 Schwer", key="gap_red"):
                update_status(df, st.session_state.current_idx, "Red", current_file)
                st.rerun()
            if col_b.button("🟢 Einfach", key="gap_green"):
                update_status(df, st.session_state.current_idx, "Green", current_file)
                st.rerun()
            
        st.markdown("---")
        c_prev, c_next = st.columns([1,1])
        if c_prev.button("⬅️ Zurück", key="gap_back", disabled=not st.session_state.history):
            prev_card()
            st.rerun()
        if c_next.button("Nächste Karte ➡️", key="gap_next", type="primary"):
            next_card()
            st.rerun()

# --- TAB 4: LISTE ---
with tab4:
    st.subheader(f"Bearbeiten: {st.session_state.current_dataset_name}")
    st.info("Klicke auf die letzte leere Zeile, um neue Wörter hinzuzufügen.")
    
    edited_df = st.data_editor(df, num_rows="dynamic", key="editor", use_container_width=True)
    
    if st.button("💾 Liste Speichern", type="primary"):
        # Leere auffüllen
        edited_df = edited_df.fillna("")
        st.session_state.vocab_df = edited_df
        save_data(edited_df, current_file)
        st.success("Gespeichert!")
        st.rerun()