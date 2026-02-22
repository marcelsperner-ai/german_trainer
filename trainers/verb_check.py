import streamlit as st
import random
import re

def clean_grammar(text):
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s*\(.*?\)', '', text).strip()

def mask_word(text, word_to_hide):
    if not isinstance(text, str) or not word_to_hide: return str(text)
    pattern = re.compile(rf'\b{re.escape(word_to_hide)}\b', re.IGNORECASE)
    if pattern.search(text):
        return pattern.sub("_______", text)
    return f"{text} (_______)"

def extract_verb(full_text):
    light_verbs = ["nehmen", "kommen", "geben", "haben", "führen", "stellen", "leisten", "treten", "bringen", "treffen", "ziehen", "machen", "halten", "zeigen", "setzen", "fallen"]
    cleaned = clean_grammar(full_text).lower()
    words = cleaned.split()
    for v in light_verbs:
        if v in words: return v
    return words[-1] if words else ""

def render(row, df, next_fn, log_event):
    v_target = extract_verb(row['Deutsch'])
    q_text = mask_word(clean_grammar(row['Deutsch']), v_target)
    
    st.markdown(f"""<div class="vocab-card">
        <div style="font-size: 14px; color: #007bff; font-weight: bold; margin-bottom: 5px;">Welches Funktionsverb passt?</div>
        <div class="main-word">{q_text}</div>
        <div class="sub-word">{row['Farsi']}</div>
    </div>""", unsafe_allow_html=True)

    if "verb_opts" not in st.session_state or st.session_state.get("verb_idx") != st.session_state.idx:
        wrong_options = ["nehmen", "geben", "machen", "stellen", "kommen", "bringen", "treffen", "halten"]
        if v_target in wrong_options: wrong_options.remove(v_target)
        opts = list(set([v_target] + random.sample(wrong_options, 3)))
        random.shuffle(opts)
        st.session_state.verb_opts = opts
        st.session_state.verb_idx = st.session_state.idx
        st.session_state.verb_solved = False

    cols = st.columns(2)
    for i, o in enumerate(st.session_state.verb_opts):
        btn_type = "primary" if st.session_state.verb_solved and o == v_target else "secondary"
        if cols[i%2].button(o, key=f"v_opt_{o}", use_container_width=True, type=btn_type):
            from app import log_event
            if o == v_target:
                st.session_state.verb_solved = True
                st.session_state.show_solution = True
                log_event(st.session_state.current_vocab_key, "verb_check", row['Deutsch'], "Correct")
                st.rerun()
            else:
                log_event(st.session_state.current_vocab_key, "verb_check", row['Deutsch'], "Incorrect")
                st.error("Das ist leider nicht das richtige Verb.")

    if st.session_state.verb_solved:
        st.success(f"Richtig! Die Verbindung lautet: **{row['Deutsch']}**")
        example_de = str(row.get('Beispielsatz', '')).strip()
        if example_de: st.info(f"Beispiel: {example_de}")