# app_phi.py - APPLICATION PRINCIPALE POUR PHI
import streamlit as st
import sys
import os

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(__file__))

def main():
    """Application principale optimisée pour Phi"""
    try:
        # Vérifier si le dashboard est initialisé
        if 'dashboard' not in st.session_state:
            from src.dashboard_phi import OracleAIDashboardPhi
            st.session_state.dashboard = OracleAIDashboardPhi()
        
        dashboard = st.session_state.dashboard
        
        # Configurer le menu
        menu = dashboard.setup_sidebar()
        
        # Afficher la page correspondante
        if menu == "home":
            dashboard.home_page()
        elif menu == "security":
            dashboard.security_page()
        elif menu == "performance":
            dashboard.performance_page()
        elif menu == "backup":
            dashboard.backup_page()
        elif menu == "chat":
            dashboard.chatbot_page()
        
        # Footer
        st.sidebar.divider()
        st.sidebar.caption("Oracle AI v2.1 • Powered by Phi • Fast & Lightweight")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Refresh page (F5) or check Ollama is running")

if __name__ == "__main__":
    main()