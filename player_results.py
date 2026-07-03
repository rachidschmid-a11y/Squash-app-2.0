import streamlit as st
import pandas as pd
from datetime import datetime
import config as cfg
import database as db

def render_player_results_page():
    st.title("🏆 Spielergebnisse eintragen & verwalten")

    st.subheader("➕ Neues Spielergebnis eintragen")
    eingetragen_von = st.selectbox("Wer trägt das Ergebnis ein?", cfg.SPIELER, key="res_input_by")
    datum = st.date_input("Spieltag", value=datetime.today(), key="res_date")

    col1, col2 = st.columns(2)
    with col1:
        spieler1 = st.selectbox("Spieler 1", cfg.SPIELER, key="p1")
    with col2:
        spieler2 = st.selectbox("Spieler 2", cfg.SPIELER, key="p2")

    if spieler1 == spieler2:
        st.warning("Spieler müssen unterschiedlich sein")

    col3, col4 = st.columns(2)
    with col3:
        punkte1 = st.number_input(f"Punkte {spieler1}", min_value=0, max_value=30, value=11, key="pts1")
    with col4:
        punkte2 = st.number_input(f"Punkte {spieler2}", min_value=0, max_value=30, value=7, key="pts2")

    if punkte1 > punkte2:
        gewinner = spieler1
    elif punkte2 > punkte1:
        gewinner = spieler2
    else:
        gewinner = None

    st.write(f"🏆 Gewinner: {gewinner if gewinner else 'Unentschieden (ungültig)'}")

    if st.button("💾 Ergebnis speichern"):
        if spieler1 == spieler2:
            st.error("Spieler dürfen nicht identisch sein")
            return
        if punkte1 == punkte2:
            st.error("Unentschieden ist nicht erlaubt")
            return

        data = {
            "gespielt_am": str(datum),
            "gewinner": gewinner,
            "verlierer": spieler2 if gewinner == spieler1 else spieler1,
            "satz_gewinner": punkte1 if gewinner == spieler1 else punkte2,
            "satz_verlierer": punkte2 if gewinner == spieler1 else punkte1,
            "eingetragen_von": eingetragen_von,
            "eingetragen_am": str(datetime.now())
        }

        db.save_spielergebnis(data)
        st.success("Ergebnis gespeichert!")
        st.rerun()

    st.divider()
    st.subheader("📋 Alle Ergebnisse")
    daten = db.get_spielergebnisse()

    if len(daten) == 0:
        st.info("Noch keine Spielergebnisse vorhanden")
        return

    df = pd.DataFrame(daten)
    st.dataframe(df, use_container_width=True)

    st.subheader("🗑 Ergebnis löschen")
    ids = df["id"].tolist()
    delete_id = st.selectbox("Spiel auswählen (ID)", ids, key="del_res_id")

    if st.button("Ergebnis Löschen"):
        db.delete_spielergebnis(delete_id)
        st.success("Gelöscht")
        st.rerun()