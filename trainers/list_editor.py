import streamlit as st
import pandas as pd

def render(row, df, next_fn, log_event):
    # WICHTIG: Auch hier muss log_event als Argument stehen, auch wenn es nicht genutzt wird!
    st.info("Hier kannst du alle Vokabeln dieses Moduls bearbeiten.")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, key=f"list_editor_grid_{st.session_state.idx}")
    
    if st.button("💾 Alle Änderungen speichern", type="primary", key=f"list_save_btn_{st.session_state.idx}"):
        edited_df.to_csv(st.session_state.loaded_file, index=False)
        st.session_state.df = edited_df
        st.success("Erfolgreich gespeichert!")