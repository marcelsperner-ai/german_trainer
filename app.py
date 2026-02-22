import streamlit as st
import pandas as pd
import random
import os
import json
import importlib.util
from datetime import datetime

# --- CONFIG & STYLES ---
st.set_page_config(page_title="Vokabeltrainer Pro v2", layout="wide")

st.markdown("""
<style>
    .main .block-container { padding: 1rem !important; }
    .vocab-card {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .main-word { font-size: 24px !important; font-weight: bold !important; color: #0E1117; }
    .sub-word { font-size: 18px !important; color: #555; margin-top: 10px; }
    .example-box { 
        background-color: #f8f9fa; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #007bff; margin-top: 20px; text-align: left; font-size: 14px;
    }
    div.stButton > button { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# --- CORE LOGIC ---

def load_registry():
    if os.path.exists("modules.json"):
        with open("modules.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"vocab_modules": {}, "training_modules": []}

def load_data(file_path):
    if not os.path.exists(file_path): return pd.DataFrame()
    df = pd.read_csv(file_path, skipinitialspace=True).fillna("")
    df.columns = [c.replace('"', '').strip() for c in df.columns]
    if 'Status' not in df.columns: df['Status'] = "Neutral"
    return df

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

def log_event(vocab_name, trainer_name, word, result):
    stats_file = "stats.csv"
    now = datetime.now()
    new_data = {
        "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Tag": now.strftime("%Y-%m-%d"),
        "Vocab_Module": vocab_name,
        "Training_Module": trainer_name,
        "Word": word,
        "Result": result
    }
    df_new = pd.DataFrame([new_data])
    if not os.path.exists(stats_file):
        df_new.to_csv(stats_file, index=False)
    else:
        df_new.to_csv(stats_file, mode='a', header=False, index=False)

def get_next_index():
    if st.session_state.df.empty: return
    if 'idx' in st.session_state and st.session_state.idx is not None:
        st.session_state.history.append(st.session_state.idx)
    df = st.session_state.df
    weights = [10 if str(s) == 'Red' else 0.5 if str(s) == 'Green' else 2 for s in df['Status']]
    st.session_state.idx = random.choices(df.index, weights=weights, k=1)[0]
    st.session_state.show_solution = False
    # Zustände der Trainer beim Wechseln eines Wortes löschen
    keys_to_del = [k for k in st.session_state.keys() if k.startswith("prep_multi_") or k.startswith("art_state_") or k.startswith("verb_state_")]
    for k in keys_to_del: del st.session_state[k]

def run_trainer_module(module_id, row, df, log_fn):
    try:
        spec = importlib.util.spec_from_file_location(module_id, f"trainers/{module_id}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.render(row, df, get_next_index, log_fn)
    except Exception as e:
        st.error(f"Fehler im Modul {module_id}: {e}")

# --- APP STATE ---
registry = load_registry()
if 'current_vocab_key' not in st.session_state:
    st.session_state.current_vocab_key = list(registry["vocab_modules"].keys())[0]
if 'history' not in st.session_state: st.session_state.history = []
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Lernen"

vocab_config = registry["vocab_modules"][st.session_state.current_vocab_key]
vocab_file = vocab_config["file"]

if 'df' not in st.session_state or st.session_state.get('loaded_file') != vocab_file:
    st.session_state.df = load_data(vocab_file)
    st.session_state.loaded_file = vocab_file
    st.session_state.idx = 0 if not st.session_state.df.empty else None
    st.session_state.show_solution = False
    st.session_state.history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("📚 Vokabeltrainer")
    st.subheader("Ansicht")
    st.session_state.view_mode = st.radio(
        "Modus:", 
        ["Lernen", "Statistik"], 
        label_visibility="collapsed", 
        key="app_main_view_selector"
    )
    st.divider()
    st.subheader("Vokabel-Module")
    selected_vocab = st.selectbox("Auswahl:", list(registry["vocab_modules"].keys()), label_visibility="collapsed", key="vocab_selector_main")
    if selected_vocab != st.session_state.current_vocab_key:
        st.session_state.current_vocab_key = selected_vocab
        st.session_state.history = []; st.rerun()
    st.divider()
    quick_edit = st.toggle("Aktuelle Karte bearbeiten", key="global_quick_edit_toggle")

# --- MAIN UI ---
if st.session_state.df.empty:
    st.warning("Keine Daten gefunden."); st.stop()

row = st.session_state.df.iloc[st.session_state.idx]

if st.session_state.view_mode == "Statistik":
    run_trainer_module("stats", row, st.session_state.df, log_event)
else:
    if quick_edit:
        with st.form("edit_form_global"):
            updated = {c: st.text_input(c, value=str(row[c]), key=f"edit_input_{c}") for c in st.session_state.df.columns if c != "Status"}
            if st.form_submit_button("Speichern"):
                for k, v in updated.items(): st.session_state.df.at[st.session_state.idx, k] = v
                save_data(st.session_state.df, st.session_state.loaded_file); st.rerun()
    else:
        allowed_ids = vocab_config.get("allowed_trainers", [])
        available = [t for t in registry["training_modules"] if t["id"] in allowed_ids and all(col in st.session_state.df.columns for col in t["required_columns"])]
        if not available: st.error("Keine Module gefunden.")
        else:
            tabs = st.tabs([t["name"] for t in available])
            for i, t in enumerate(available):
                with tabs[i]:
                    st.session_state.active_trainer_id = t["id"]
                    run_trainer_module(t["id"], row, st.session_state.df, log_event)

    # Global Navigation
    st.divider()
    state_key_prep = f"prep_multi_{st.session_state.idx}"
    state_key_art = f"art_state_{st.session_state.idx}"
    is_solved = (st.session_state.get('show_solution', False) or 
                 st.session_state.get(state_key_prep, {}).get('finished', False) or
                 st.session_state.get(state_key_art, {}).get('finished', False))

    if not quick_edit:
        # Wir nutzen 4 Spalten, wenn gelöst, sonst 2 für Back/Next
        if is_solved:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            if c1.button("⬅️", key=f"nav_back_{st.session_state.idx}"):
                if st.session_state.history:
                    st.session_state.idx = st.session_state.history.pop()
                    st.session_state.show_solution = False; st.rerun()
            if c2.button("🔴", key=f"rate_hard_{st.session_state.idx}"):
                log_event(st.session_state.current_vocab_key, st.session_state.active_trainer_id, row['Deutsch'], "Incorrect")
                st.session_state.df.at[st.session_state.idx, 'Status'] = "Red"
                save_data(st.session_state.df, st.session_state.loaded_file); get_next_index(); st.rerun()
            if c3.button("🟢", key=f"rate_easy_{st.session_state.idx}"):
                log_event(st.session_state.current_vocab_key, st.session_state.active_trainer_id, row['Deutsch'], "Correct")
                st.session_state.df.at[st.session_state.idx, 'Status'] = "Green"
                save_data(st.session_state.df, st.session_state.loaded_file); get_next_index(); st.rerun()
            if c4.button("➡️", key=f"nav_next_{st.session_state.idx}"):
                get_next_index(); st.rerun()
        else:
            c1, c2 = st.columns([1, 1])
            if c1.button("⬅️", key=f"nav_back_unsolved_{st.session_state.idx}", disabled=not st.session_state.history):
                st.session_state.idx = st.session_state.history.pop()
                st.session_state.show_solution = False; st.rerun()
            if c2.button("➡️", key=f"nav_next_unsolved_{st.session_state.idx}"):
                get_next_index(); st.rerun()