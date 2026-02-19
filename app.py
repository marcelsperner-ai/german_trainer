import streamlit as st
import pandas as pd
import random
import re
import os
import json

# --- CONFIG & CSS ---
st.set_page_config(page_title="Vokabeltrainer Pro", layout="wide")

st.markdown("""
<style>
    .main .block-container { padding: 0.5rem 0.5rem !important; }
    .vocab-card {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .main-word { font-size: 20px !important; font-weight: bold !important; color: #0E1117; }
    .sub-word { font-size: 17px !important; color: #555; margin-top: 8px; }
    .example-box { 
        background-color: #f0f4f8; 
        padding: 12px; 
        border-radius: 10px; 
        border-left: 5px solid #007bff; 
        margin-top: 15px; 
        text-align: left; 
        font-size: 14px; 
        line-height: 1.4;
    }
    div.stButton > button { width: 100% !important; border-radius: 10px !important; height: 3em !important; font-size: 13px !important; }
    [data-testid="stSidebar"] div.stButton > button { height: 2.2em !important; font-size: 11px !important; text-align: left !important; }
    button[data-baseweb="tab"] { font-size: 11px !important; padding: 0px 5px !important; }
</style>
""", unsafe_allow_html=True)

# --- HILFSFUNKTIONEN ---

def clean_grammar(text):
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def mask_word(text, word_to_hide):
    if not isinstance(text, str) or not word_to_hide: return str(text)
    pure_word = str(word_to_hide).split('+')[0].strip()
    if not pure_word or pure_word == "–": return text
    pattern = re.compile(rf'\b{re.escape(pure_word)}\b', re.IGNORECASE)
    if pattern.search(text):
        return pattern.sub("_______", text)
    return f"{text} (_______)"

def parse_prep_info(prep_str):
    prep_str = str(prep_str)
    if not prep_str or "+" not in prep_str: return prep_str, "Unbekannt"
    parts = prep_str.split('+')
    prep = parts[0].strip()
    k_code = parts[1].strip().upper()
    kasus = "Dativ" if "D" in k_code else "Akkusativ" if "A" in k_code else "Genitiv" if "G" in k_code else "Unbekannt"
    return prep, kasus

def extract_verb(full_text):
    light_verbs = ["nehmen", "kommen", "geben", "haben", "führen", "stellen", "leisten", "treten", "bringen", "treffen", "ziehen", "machen", "halten", "zeigen", "setzen", "fallen"]
    cleaned = clean_grammar(full_text).lower()
    words = cleaned.split()
    for v in light_verbs:
        if v in words: return v
    return words[-1] if words else ""

def show_example(row):
    if str(row.get('Beispielsatz', '')).strip():
        st.markdown(f"""<div class="example-box">
            <b>Kontext / Beispiel:</b><br>
            <span style="color: #1a1a1a;">{row['Beispielsatz']}</span><br>
            <i style="color: #555;">{row.get('Beispielsatz_Farsi', '')}</i>
        </div>""", unsafe_allow_html=True)

def get_pons_url(word):
    query = clean_grammar(word).replace(" ", "+")
    return f"https://de.pons.com/text-%C3%BCbersetzung/deutsch-persisch?q={query}"

# --- DATA LOGIC ---

def load_data(file):
    if not os.path.exists(file): return pd.DataFrame()
    try:
        df = pd.read_csv(file, on_bad_lines='skip').fillna("")
        df.columns = [c.replace('"', '').strip() for c in df.columns]
        if not df.empty:
            df = df[df['Deutsch'].astype(str).str.lower() != 'deutsch']
            df = df[df['Deutsch'].astype(str).str.strip() != '']
        if 'Status' not in df.columns: df['Status'] = "Neutral"
        return df.reset_index(drop=True)
    except:
        return pd.DataFrame()

# --- INITIALISIERUNG ---
if os.path.exists("modules.json"):
    with open("modules.json", 'r', encoding='utf-8') as f:
        modules = json.load(f)
else:
    modules = {"Standard": "vokabeln.csv"}

if 'current_mod' not in st.session_state:
    st.session_state.current_mod = list(modules.keys())[0]

current_file = modules[st.session_state.current_mod]

if 'df' not in st.session_state or st.session_state.get('last_file') != current_file:
    st.session_state.df = load_data(current_file)
    st.session_state.last_file = current_file
    st.session_state.idx = 0 if not st.session_state.df.empty else None
    st.session_state.show = False
    st.session_state.hist = []

def get_next():
    if st.session_state.df is None or st.session_state.df.empty: return
    st.session_state.hist.append(st.session_state.idx)
    df_curr = st.session_state.df
    weights = [10 if str(s) == 'Red' else 0.2 if str(s) == 'Green' else 2 for s in df_curr['Status']]
    st.session_state.idx = random.choices(df_curr.index, weights=weights, k=1)[0]
    st.session_state.show = False

# --- SIDEBAR ---
with st.sidebar:
    st.title("📚 Module")
    for mod_name in sorted(modules.keys()):
        is_active = st.session_state.current_mod == mod_name
        if st.button(mod_name, key=f"nav_{mod_name}", type="primary" if is_active else "secondary"):
            st.session_state.current_mod = mod_name
            st.rerun()

# --- MAIN APP ---
df = st.session_state.df
if df is None or df.empty:
    st.error("Keine Daten geladen.")
    st.stop()

row = df.loc[st.session_state.idx]
has_prep_col = "Präposition" in df.columns and any(str(x).strip() != "" and str(x).strip() != "–" for x in df["Präposition"])
has_expl_col = "Erläuterung" in df.columns

# --- EINZIGE TAB-ERSTELLUNG ---
tab_list = ["🃏 Karte"]
if has_prep_col: tab_list += ["🎯 Präp", "⚖️ Kasus"]
if has_expl_col: tab_list += ["🧩 Verb", "✍️ Syn"]
if not has_prep_col and not has_expl_col: tab_list += ["✍️ Üben", "🧩 Lücke"]
tab_list += ["🔍 PONS", "📝 Liste"]

tabs = st.tabs(tab_list)

def card_display(main, sub, info="", color="none"):
    border_color = "#28a745" if color == "green" else "#dc3545" if color == "red" else "#f0f2f6"
    st.markdown(f"""<div class="vocab-card" style="border-color: {border_color}">
        <div class="main-word">{main}</div><div class="sub-word">{sub}</div>
        <div style="font-size: 11px; color: gray; margin-top: 8px;">{info}</div></div>""", unsafe_allow_html=True)

# --- TAB INHALTE ---
current_tab_idx = 0

# 1. Karte
with tabs[current_tab_idx]:
    if not st.session_state.show:
        card_display(row['Farsi'], "???", "Wie lautet der deutsche Ausdruck?")
        if st.button("Lösung zeigen", type="primary", key="sh1"): st.session_state.show = True; st.rerun()
    else:
        info = f"{row.get('Präposition', '')} | {row.get('Erläuterung', '')}".strip(" | ")
        card_display(row['Deutsch'], row['Farsi'], info)
        show_example(row)
        c1, c2 = st.columns(2)
        if c1.button("🔴 Schwer", key="fc_r"):
            df.at[st.session_state.idx, 'Status'] = "Red"; get_next(); st.rerun()
        if c2.button("🟢 Einfach", key="fc_g"):
            df.at[st.session_state.idx, 'Status'] = "Green"; get_next(); st.rerun()
current_tab_idx += 1

# 2. Präp & Kasus
if has_prep_col:
    with tabs[current_tab_idx]: # Präp-Check
        t_prep, _ = parse_prep_info(row['Präposition'])
        q_text = mask_word(clean_grammar(row['Deutsch']), t_prep)
        card_display(q_text, "_______", row['Farsi'])
        preps = ["an", "auf", "für", "in", "mit", "nach", "über", "um", "von", "zu", "vor", "gegen"]
        opts = list(set([t_prep.split('/')[0].strip()] + random.sample(preps, 3)))
        random.shuffle(opts)
        cols = st.columns(2)
        for i, o in enumerate(opts):
            if cols[i%2].button(o, key=f"p_{o}"):
                if o in t_prep and o != "": 
                    st.success(f"Richtig! {row['Präposition']}"); show_example(row)
                    if st.button("Nächste", on_click=get_next, key="n_p"): st.rerun()
                else: st.error("Falsch!")
    current_tab_idx += 1
    
    with tabs[current_tab_idx]: # Kasus-Check
        _, t_kasus = parse_prep_info(row['Präposition'])
        card_display(f"{clean_grammar(row['Deutsch'])}", "???", "Welcher Kasus folgt?")
        c1, c2 = st.columns(2)
        if c1.button("Akkusativ", key="k_akk"):
            if "Akkusativ" in t_kasus: st.success("Richtig!"); show_example(row); st.button("Weiter", on_click=get_next, key="n_k1")
            else: st.error("Falsch!")
        if c2.button("Dativ", key="k_dat"):
            if "Dativ" in t_kasus: st.success("Richtig!"); show_example(row); st.button("Weiter", on_click=get_next, key="n_k2")
            else: st.error("Falsch!")
    current_tab_idx += 1

# 3. Verb & Syn
if has_expl_col:
    with tabs[current_tab_idx]: # Verb-Check
        v_target = extract_verb(row['Deutsch'])
        q_text = mask_word(clean_grammar(row['Deutsch']), v_target)
        card_display(q_text, row['Farsi'], "Welches Verb passt?")
        v_opts = list(set([v_target] + random.sample(["nehmen", "geben", "machen", "stellen", "kommen", "bringen"], 3)))
        random.shuffle(v_opts)
        cols = st.columns(2)
        for i, o in enumerate(v_opts):
            if cols[i%2].button(o, key=f"v_{o}"):
                if o == v_target: 
                    st.success(f"Richtig: {row['Deutsch']}"); show_example(row)
                    st.button("Nächste", on_click=get_next, key="n_v")
                else: st.error("Falsch!")
    current_tab_idx += 1
    
    with tabs[current_tab_idx]: # Synonym
        card_display(row.get('Erläuterung', 'Synonym'), "???", row['Farsi'])
        if st.button("Lösung aufdecken", key="sl_btn"):
            st.info(row['Deutsch']); show_example(row)
            st.button("Weiter", on_click=get_next, key="n_s")
    current_tab_idx += 1

# 4. Standard (wenn keine Präp/Expl)
if not has_prep_col and not has_expl_col:
    with tabs[current_tab_idx]: # Standard Üben
        card_display(row['Farsi'], "Übersetze...", "Deutsch gesucht")
        u_in = st.text_input("Eingabe:", key="u_in").strip().lower()
        if st.button("Prüfen"):
            if not u_in: st.warning("⚠️ Keine Eingabe")
            elif u_in in clean_grammar(row['Deutsch']).lower(): 
                st.success("Richtig!"); show_example(row)
            else: st.error(f"Falsch! Lösung: {row['Deutsch']}")
            st.button("Nächste ➡️", on_click=get_next, key="n_std")
    current_tab_idx += 1
    
    with tabs[current_tab_idx]: # Lückentext
        sentence = str(row.get('Beispielsatz', ''))
        term = clean_grammar(row['Deutsch'])
        masked_sentence = sentence.replace(term, "_______") if term in sentence else sentence
        card_display("Lückentext", masked_sentence, row['Farsi'])
        if st.button("Lösung"):
            st.write(f"Lösung: {row['Deutsch']}"); show_example(row)
            st.button("Weiter", on_click=get_next)
    current_tab_idx += 1

# 5. PONS
with tabs[current_tab_idx]:
    st.subheader(f"PONS Analyse: {clean_grammar(row['Deutsch'])}")
    pons_url = get_pons_url(row['Deutsch'])
    st.markdown(f"[Direkt bei PONS öffnen]({pons_url})")
    st.components.v1.iframe(pons_url, height=600, scrolling=True)
current_tab_idx += 1

# 6. Liste
with tabs[current_tab_idx]:
    edited = st.data_editor(df, use_container_width=True, hide_index=True)
    if st.button("💾 Speichern"):
        edited.to_csv(current_file, index=False); st.success("Gespeichert!")

# --- NAV UNTEN ---
st.divider()
c1, c2 = st.columns(2)
if c1.button("⬅️ Zurück", disabled=not st.session_state.hist, key="nav_p"):
    st.session_state.idx = st.session_state.hist.pop(); st.rerun()
if c2.button("Überspringen ➡️", on_click=get_next, key="nav_next"): st.rerun()