import pandas as pd
from datetime import datetime
import database as db
import config as cfg

def format_dataframe(df):
    df_clean = df.copy()
    if "gespielt_am" in df_clean.columns:
        df_clean["gespielt_am"] = pd.to_datetime(df_clean["gespielt_am"]).dt.strftime('%d.%m.%Y')
    if "eingetragen_am" in df_clean.columns:
        df_clean["eingetragen_am"] = pd.to_datetime(df_clean["eingetragen_am"]).dt.strftime('%d.%m.%Y %H:%M')
    cols = [c for c in cfg.ORDERED_COLUMNS if c in df_clean.columns]
    return df_clean[cols]

def speichern_logik(spieler, einheiten, eingetragen_von, gespielt_am):
    karte = db.get_karte()
    if karte is None:
        return False, "Keine aktive Karte vorhanden"

    kosten_fuer_spiel = einheiten * cfg.PLATZPREIS * cfg.FAKTOR
    muss_abgerechnet_werden = karte["guthaben"] < kosten_fuer_spiel
    kosten_pro_person = kosten_fuer_spiel / len(spieler)

    for person in spieler:
        db.insert_spiel({
            "spieler": person,
            "einheiten": einheiten,
            "kosten": kosten_pro_person, 
            "eingetragen_von": eingetragen_von,
            "eingetragen_am": datetime.now().isoformat(),
            "gespielt_am": gespielt_am.isoformat(),
            "abgerechnet": False 
        })

    neues_guthaben = karte["guthaben"] - kosten_fuer_spiel
    db.update_karte_guthaben(karte["id"], neues_guthaben)

    if muss_abgerechnet_werden:
        abrechnung_logik(karte)
        return True, "⚠️ Guthaben aufgebraucht! Das Spiel wird noch verbucht, danach wird die Karte automatisch abgerechnet."
    
    return False, "Erfolgreich verarbeitet!"

def abrechnung_logik(karte):
    daten = db.get_spiele()
    if len(daten) == 0: return

    df = pd.DataFrame(daten)
    summen_einheiten = df.groupby("spieler")["einheiten"].sum()
    total_einheiten = summen_einheiten.sum()
    payer = karte.get("bezahlt_von", "dem Zahler")
    
    for name, einheiten in summen_einheiten.items():
        anteil = einheiten / total_einheiten
        schulden = round(anteil * cfg.KARTEN_WERT, 2)
        
        db.insert_abrechnung({
            "spieler": name, 
            "betrag": float(schulden),
            "karte_id": karte["id"]
        })

    db.set_spiele_abgerechnet()
    db.set_karte_inaktiv(karte["id"])

def build_dataframe():
    data = db.get_spielergebnisse()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def filter_matchups(df, spieler):
    gegner_liste = [s for s in cfg.SPIELER if s != spieler]
    matchups = {}
    for g in gegner_liste:
        daten = df[
            ((df["gewinner"] == spieler) & (df["verlierer"] == g)) |
            ((df["gewinner"] == g) & (df["verlierer"] == spieler))
        ].copy()
        if len(daten) > 0:
            matchups[g] = daten
    return matchups

def player_stats(df, spieler):
    spiele = df[(df["gewinner"] == spieler) | (df["verlierer"] == spieler)]
    siege = len(spiele[spiele["gewinner"] == spieler])
    niederlagen = len(spiele[spiele["verlierer"] == spieler])
    gesamt = siege + niederlagen
    quote = (siege / gesamt * 100) if gesamt > 0 else 0
    return {
        "siege": siege,
        "niederlagen": niederlagen,
        "gesamt": gesamt,
        "quote": round(quote, 1)
    }

def head_to_head_matrix(df):
    matrix = {}
    for p1 in cfg.SPIELER:
        matrix[p1] = {}
        for p2 in cfg.SPIELER:
            if p1 == p2:
                matrix[p1][p2] = None
                continue
            matches = df[(df["gewinner"] == p1) & (df["verlierer"] == p2)]
            matrix[p1][p2] = len(matches)
    return pd.DataFrame(matrix).fillna(0)