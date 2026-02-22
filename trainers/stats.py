import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

def render(row, df, next_fn, log_event):
    # WICHTIG: Auch hier muss log_event als viertes Argument akzeptiert werden.
    
    st.subheader("📊 Lernstatistik")
    stats_file = "stats.csv"
    
    if not os.path.exists(stats_file):
        st.info("Noch keine Daten vorhanden. Lerne ein paar Wörter, um die Statistik zu füllen!")
        return

    # Daten laden
    try:
        data = pd.read_csv(stats_file)
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Tag'] = pd.to_datetime(data['Tag']).dt.date
        
        # --- BEREINIGUNG ---
        # Wir schließen den List-Editor und das Statistik-Modul selbst aus den Daten aus,
        # da dies keine echten Trainings-Interaktionen sind.
        exclude_modules = ["list_editor", "stats"]
        data = data[~data['Training_Module'].isin(exclude_modules)]
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Statistik: {e}")
        return

    if data.empty:
        st.info("Bisher wurden noch keine Trainings-Ergebnisse aufgezeichnet.")
        return

    # --- FILTER MENÜ ---
    c1, c2 = st.columns(2)
    v_filter = c1.multiselect(
        "Vokabel-Module", 
        options=sorted(data['Vocab_Module'].unique()), 
        default=data['Vocab_Module'].unique(),
        key="stats_v_filter"
    )
    t_filter = c2.multiselect(
        "Trainings-Module", 
        options=sorted(data['Training_Module'].unique()), 
        default=data['Training_Module'].unique(),
        key="stats_t_filter"
    )
    
    filtered_data = data[data['Vocab_Module'].isin(v_filter) & data['Training_Module'].isin(t_filter)]

    if filtered_data.empty:
        st.warning("Keine Daten für diese Filterkombination gefunden.")
        return

    # --- SESSION LOGIK: Dubletten innerhalb eines Tages/Trainers filtern ---
    session_data = filtered_data.sort_values('Timestamp').drop_duplicates(
        subset=['Tag', 'Training_Module', 'Word'], 
        keep='last'
    )

    # --- METRIKEN BERECHNEN ---
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    def get_stats(df_period):
        total = len(df_period)
        correct = len(df_period[df_period['Result'] == 'Correct'])
        wrong = len(df_period[df_period['Result'] == 'Incorrect'])
        perc = (correct / total * 100) if total > 0 else 0
        return total, correct, wrong, perc

    st.divider()
    
    # Tabs für Zeiträume
    t_today, t_week, t_month, t_all = st.tabs(["Heute", "Diese Woche", "Diesen Monat", "Gesamt"])

    periods = [
        (t_today, session_data[session_data['Tag'] == today]),
        (t_week, session_data[session_data['Tag'] >= start_week]),
        (t_month, session_data[session_data['Tag'] >= start_month]),
        (t_all, session_data)
    ]

    for tab, df_p in periods:
        with tab:
            total, correct, wrong, perc = get_stats(df_p)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Gelernt", total)
            m2.metric("Richtig", correct)
            m3.metric("Falsch", wrong)
            m4.metric("Erfolg", f"{perc:.1f}%")
            
            if not df_p.empty:
                # Aktivitäten-Chart
                daily_counts = df_p.groupby('Tag').size().reset_index(name='Anzahl')
                st.line_chart(daily_counts.set_index('Tag'))

    st.divider()
    with st.expander("Details der gefilterten Session anzeigen"):
        st.dataframe(
            session_data.sort_values('Timestamp', ascending=False), 
            use_container_width=True
        )