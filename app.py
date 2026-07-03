import streamlit as st
import ui
import player_results

def main():
    st.sidebar.title("🏸 Squash Hub")
    st.sidebar.markdown("Wähle ein Modul aus:")
    
    wahl = st.sidebar.radio(
        "Navigation",
        ["💰 Abrechnung & Guthaben", "🏆 Matches eintragen", "📊 Sportliche Statistiken"]
    )
    
    st.sidebar.divider()
    st.sidebar.caption("Gekoppelt mit Supabase Live-Datenbank.")

    # Zentrales Modul-Routing
    if wahl == "💰 Abrechnung & Guthaben":
        ui.render_abrechnung_page()
    elif wahl == "🏆 Matches eintragen":
        player_results.render_player_results_page()
    elif wahl == "📊 Sportliche Statistiken":
        ui.render_statistics_page()

if __name__ == "__main__":
    main()