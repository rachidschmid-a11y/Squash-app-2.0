import streamlit as st
from supabase import create_client

# Supabase Verbindung herstellen
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- FINANZ-QUERIES (ex app.py) ---

def get_karte():
    try:
        result = supabase.table("karte").select("*").eq("aktiv", True).execute()
        return result.data[0] if len(result.data) > 0 else None
    except Exception as e:
        st.error(f"Fehler beim Laden der Karte: {e}")
        return None

def get_spiele():
    try:
        result = supabase.table("spiele").select("*").eq("abgerechnet", False).order("id", desc=True).execute()
        return result.data or []
    except Exception as e:
        st.error(f"Fehler beim Laden der Spiele: {e}")
        return []

def get_letzte_abrechnung():
    try:
        last_card_res = supabase.table("karte").select("*").eq("aktiv", False).order("id", desc=True).limit(1).execute()
        if not last_card_res.data:
            return [], "Unbekannt"
        
        last_card = last_card_res.data[0]
        payer = last_card.get("bezahlt_von", "dem Zahler")
        last_card_id = last_card["id"]

        result = supabase.table("abrechnung").select("*").eq("karte_id", last_card_id).execute()
        return result.data or [], payer
    except Exception as e:
        st.error(f"Fehler beim Laden der letzten Abrechnung: {e}")
        return [], "Unbekannt"

def insert_spiel(data: dict):
    return supabase.table("spiele").insert(data).execute()

def update_karte_guthaben(karte_id, neues_guthaben):
    return supabase.table("karte").update({"guthaben": neues_guthaben}).eq("id", karte_id).execute()

def insert_abrechnung(data: dict):
    return supabase.table("abrechnung").insert(data).execute()

def set_spiele_abgerechnet():
    return supabase.table("spiele").update({"abgerechnet": True}).eq("abgerechnet", False).execute()

def set_karte_inaktiv(karte_id):
    return supabase.table("karte").update({"aktiv": False}).eq("id", karte_id).execute()

def insert_karte(data: dict):
    return supabase.table("karte").insert(data).execute()

def delete_spiel_by_id(spiel_id):
    return supabase.table("spiele").delete().eq("id", spiel_id).execute()

def update_karte_zahler(karte_id, neuer_zahler):
    """Aktualisiert den Zahler einer bestehenden Karte im Falle eines Tippfehlers."""
    try:
        return supabase.table("karte").update({"bezahlt_von": neuer_zahler}).eq("id", karte_id).execute()
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren des Zahlers in der Datenbank: {e}")
        return None

# --- SPORT-QUERIES (ex Auswertung.py) ---

def get_spielergebnisse():
    try:
        result = supabase.table("spielergebnisse").select("*").order("gespielt_am", desc=True).execute()
        return result.data or []
    except Exception as e:
        st.error("Fehler beim Laden der Spielergebnisse")
        st.write(e)
        return []

def save_spielergebnis(data: dict):
    try:
        supabase.table("spielergebnisse").insert(data).execute()
        return True
    except Exception as e:
        st.error("Fehler beim Speichern des Spielergebnisses in Supabase:")
        st.write(e)
        return False

def delete_spielergebnis(result_id: int):
    try:
        supabase.table("spielergebnisse").delete().eq("id", result_id).execute()
        return True
    except Exception as e:
        st.error("Fehler beim Löschen")
        st.write(e)
        return False
