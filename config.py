import streamlit as st

# Globale Spielerliste
SPIELER = ["Jonas", "Marlon", "Paul", "Vossi"]

# Finanz-Parameter für Abrechnungslogik
PLATZPREIS = 19
FAKTOR = 200 / 250
KARTEN_WERT = 200.0

# Sortierungs-Reihenfolge für Tabellen-Anzeigen
ORDERED_COLUMNS = ["eingetragen_von", "gespielt_am", "spieler", "eingetragen_am", "einheiten", "kosten"]