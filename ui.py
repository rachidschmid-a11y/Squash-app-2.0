import streamlit as st
import pandas as pd
from datetime import datetime, date
import config as cfg
import database as db
import calculations as calc
import visualizations as vis

def render_abrechnung_page():
    st.title("🏸 Squash Abrechnung & Guthaben")

    with st.expander("➕ Neue Karte starten"):
        st.markdown("#### 📋 Letzte Abrechnung (Historie)")
        letzte_schulden, alter_zahler = db.get_letzte_abrechnung()
        
        if letzte_schulden:
            st.caption(f"Zur Erinnerung: Das waren die Ausgleichszahlungen für die letzte Karte von **{alter_zahler}**:")
            for eintrag in letzte_schulden:
                if eintrag['spieler'] != alter_zahler:
                    st.write(f"• **{eintrag['spieler']}** → **{eintrag['betrag']:.2f} €** an {alter_zahler}")
                else:
                    st.write(f"• *{eintrag['spieler']} (Zahler der Karte)*")
        else:
            st.info("Keine historischen Abrechnungsdaten gefunden.")
            
        st.divider()
        
        st.markdown("#### Neue Karte aktivieren")
        bezahlt_von = st.selectbox("Wer hat die Karte bezahlt?", cfg.SPIELER, key="card_payer")
        
        if st.button("Karte aktivieren"):
            last_card = db.supabase.table("karte").select("*").eq("aktiv", False).order("id", desc=True).limit(1).execute()
            last_guthaben = last_card.data[0]["guthaben"] if (last_card.data and last_card.data[0].get("guthaben") is not None) else 0
            
            start_guthaben = 250.0 + (last_guthaben if last_guthaben < 0 else 0)
            
            db.insert_karte({
                "guthaben": start_guthaben, 
                "aktiv": True, 
                "bezahlt_von": bezahlt_von
            })
            
            st.success(f"Neue Karte gestartet! Bezahlt von: {bezahlt_von}")
            st.rerun()

    st.divider()
    st.subheader("Neues Spiel (Session) eintragen")
    col1, col2 = st.columns(2)
    with col1:
        eingetragen_von = st.selectbox("Eingetragen von", cfg.SPIELER, key="fin_input_by")
    with col2:
        gespielt_am = st.date_input("Gespielt am", date.today(), key="fin_date")

    st.write("**Mitspieler auswählen:**")
    cols = st.columns(4)
    auswahl = [p for i, p in enumerate(cfg.SPIELER) if cols[i].checkbox(p, key=f"check_{p}")]

    einheiten = st.number_input("Einheiten (45 Minuten)", min_value=1, max_value=20, value=1, key="fin_units")

    if st.button("Spiel-Session speichern"):
        if len(auswahl) == 0:
            st.warning("Bitte Spieler auswählen")
        else:
            muss_aufraeumen, msg = calc.speichern_logik(auswahl, einheiten, eingetragen_von, gespielt_am)
            if muss_aufraeumen:
                st.info(msg)
            else:
                st.success(msg)
            st.rerun()

    st.divider()
    st.subheader("Aktueller Stand")
    karte = db.get_karte()
    if karte:
        st.metric("Kartenguthaben", f"{karte['guthaben']:.2f} €")
        st.caption(f"Diese Karte wurde bezahlt von: **{karte.get('bezahlt_von', 'Unbekannt')}**")
        
        # Funktion zur nachträglichen Korrektur des Karten-Zahlers bei Tippfehlern
        with st.expander("✏️ Falschen Zahler eingetragen? Name korrigieren"):
            aktueller_zahler = karte.get("bezahlt_von")
            default_index = cfg.SPIELER.index(aktueller_zahler) if aktueller_zahler in cfg.SPIELER else 0
            
            neuer_zahler = st.selectbox(
                "Wer hat die Karte wirklich bezahlt?", 
                cfg.SPIELER, 
                index=default_index, 
                key="correct_card_payer"
            )
            
            if st.button("Zahler aktualisieren", key="btn_correct_payer"):
                if neuer_zahler == aktueller_zahler:
                    st.info("Dieser Spieler ist bereits als Zahler eingetragen.")
                else:
                    db.update_karte_zahler(karte["id"], neuer_zahler)
                    st.success(f"Zahler erfolgreich auf **{neuer_zahler}** geändert!")
                    st.rerun()
    else:
        st.warning("Keine aktive Karte vorhanden. Bitte neue Karte starten.")

    spiele = db.get_spiele()
    if spiele:
        df_display = calc.format_dataframe(pd.DataFrame(spiele))
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Noch keine Spiele auf der aktuellen Karte vorhanden")

    st.divider()
    with st.expander("Fehlerhaften Eintrag korrigieren / löschen"):
        if spiele:
            df_raw = pd.DataFrame(spiele)
            optionen = {row["id"]: f"ID {row['id']} | {pd.to_datetime(row['gespielt_am']).strftime('%d.%m.%Y')} | {row['spieler']} | {row['kosten']:.2f} €" for _, row in df_raw.iterrows()}
            auswahl_id = st.selectbox("Welcher Eintrag soll gelöscht werden?", list(optionen.keys()), format_func=lambda x: optionen[x], key="del_fin_id")
            
            if st.button("Eintrag löschen & Guthaben erstatten"):
                eintrag = next((s for s in spiele if s["id"] == auswahl_id), None)
                if eintrag and karte:
                    db.update_karte_guthaben(karte["id"], karte["guthaben"] + eintrag.get("kosten", 0))
                db.delete_spiel_by_id(auswahl_id)
                st.success(f"Eintrag {auswahl_id} erfolgreich gelöscht!")
                st.rerun()
        else:
            st.info("Keine aktuellen Spiele vorhanden, die gelöscht werden könnten.")

    st.divider()
    st.subheader("Kostenstatistik")
    if spiele:
        df_stats = pd.DataFrame(spiele).groupby("spieler")["kosten"].sum().reset_index()
        c1, c2 = st.columns(2)
        with c1:
            vis.plot_costs_bar(df_stats)
        with c2:
            vis.plot_costs_pie(df_stats)
    else:
        st.info("Noch keine Daten für eine Visualisierung vorhanden.")

def render_statistics_page():
    st.title("📊 Sportliche Statistiken")

    df = calc.build_dataframe()
    if df.empty:
        st.info("Noch keine Daten vorhanden")
        return

    spieler = st.selectbox("Spieler auswählen", cfg.SPIELER, key="stats_player_select")

    stats = calc.player_stats(df, spieler)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Siege", stats["siege"])
    col2.metric("Niederlagen", stats["niederlagen"])
    col3.metric("Spiele", stats["gesamt"])
    col4.metric("Quote %", stats["quote"])

    st.divider()
    vis.plot_match_scatter(df, spieler)

    st.subheader("🧮 Gesamt-Matrix")
    matrix = calc.head_to_head_matrix(df)
    st.dataframe(matrix, use_container_width=True)
