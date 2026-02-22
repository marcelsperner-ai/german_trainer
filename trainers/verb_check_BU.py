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

def render(row, df, next_fn):
    v_target = extract_verb(row['Deutsch'])
    q_text = mask_word(clean_grammar(row['Deutsch']), v_target)
    
    st.markdown(f"""<div class="vocab-card">
        <div class="main-word">{q_text}</div>
        <div class="sub-word">{row['Farsi']}</div>
        <div style="font-size: 12px; color: gray; margin-top: 10px;">Welches Funktionsverb passt?</div>
    </div>""", unsafe_allow_html=True)

    # Generate options
    wrong_options = ["nehmen", "geben", "machen", "stellen", "kommen", "bringen", "treffen", "halten"]
    if v_target in wrong_options:
        wrong_options.remove(v_target)
    
    v_opts = list(set([v_target] + random.sample(wrong_options, 3)))
    random.shuffle(v_opts)
    
    cols = st.columns(2)
    for i, o in enumerate(v_opts):
        if cols[i%2].button(o, key=f"v_opt_{o}", use_container_width=True):
            if o == v_target:
                st.success(f"Richtig! Die Verbindung lautet: {row['Deutsch']}")
                if str(row.get('Beispielsatz', '')).strip():
                    st.info(f"Beispiel: {row['Beispielsatz']}")
                
                if st.button("Weiter", type="primary"):
                    next_fn()
                    st.rerun()
            else:
                st.error("Das ist leider nicht das richtige Verb.")