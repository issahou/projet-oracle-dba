# main.py (version corrigée)
import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

# Ajouter le répertoire courant au path
sys.path.append(str(Path(__file__).parent))

def check_oracle_client():
    """Vérifie si Oracle Client est installé"""
    import platform
    
    print("🔍 Vérification de Oracle Client...")
    
    if platform.system() == "Windows":
        # Chemins communs pour Oracle Instant Client sur Windows
        common_paths = [
            r"C:\Oracle\instantclient_21_10",
            r"C:\Oracle\instantclient_19_18",
            r"C:\instantclient_21_10",
            r"C:\instantclient_19_18",
            os.environ.get("ORACLE_HOME", ""),
            os.environ.get("TNS_ADMIN", ""),
        ]
        
        for path in common_paths:
            if path and os.path.exists(path):
                dll_path = os.path.join(path, "oci.dll")
                if os.path.exists(dll_path):
                    print(f"✅ Oracle Client trouvé: {path}")
                    # Ajouter au PATH pour cx_Oracle
                    os.environ["PATH"] = path + ";" + os.environ["PATH"]
                    return True
        
        print("❌ Oracle Client non trouvé. Mode démonstration activé.")
        return False
    else:
        print("⚠️  Système non-Windows détecté, vérification Oracle Client limitée")
        return False

def create_mock_data():
    """Crée des données de test pour le développement"""
    from datetime import datetime, timedelta
    import numpy as np
    
    print("📊 Création de données de test...")
    
    # Logs d'audit fictifs
    audit_data = []
    for i in range(100):
        timestamp = datetime.now() - timedelta(hours=i)
        audit_data.append({
            'USERID': f'USER_{i % 10}',
            'USERHOST': f'host{i % 5}',
            'TERMINAL': f'term{i % 3}',
            'TIMESTAMP': timestamp,
            'ACTION': [100, 101, 2, 3, 6][i % 5],  # LOGON, LOGOFF, INSERT, SELECT, UPDATE
            'RETURNCODE': 0 if i < 90 else 1017,  # Succès ou échec d'authentification
            'OBJECT_OWNER': f'OWNER_{i % 3}',
            'OBJECT_NAME': f'TABLE_{i % 5}',
            'SESSION_ID': i,
            'ENTRY_ID': i * 100,
            'COMMENT': f'Commentaire {i}'
        })
    
    return {
        'audit_logs': pd.DataFrame(audit_data),
        'performance_metrics': {
            'slow_queries': pd.DataFrame({
                'SQL_ID': [f'SQL_{i}' for i in range(10)],
                'SQL_TEXT': [f'SELECT * FROM table_{i}' for i in range(10)],
                'ELAPSED_TIME': [1000000 + i * 500000 for i in range(10)],
                'CPU_TIME': [500000 + i * 250000 for i in range(10)],
                'EXECUTIONS': [100, 50, 200, 75, 150, 80, 120, 90, 180, 60]
            }),
            'system_events': pd.DataFrame({
                'EVENT': ['db file sequential read', 'db file scattered read', 
                         'log file sync', 'CPU time', 'latch free'],
                'TIME_WAITED': [1000000, 800000, 600000, 400000, 200000]
            })
        },
        'security_config': {
            'users': pd.DataFrame({
                'USERNAME': ['ADMIN', 'APP_USER', 'READ_ONLY', 'REPORT_USER'],
                'ACCOUNT_STATUS': ['OPEN', 'OPEN', 'LOCKED', 'EXPIRED'],
                'PROFILE': ['DEFAULT', 'APP_PROFILE', 'DEFAULT', 'DEFAULT']
            })
        },
        'timestamp': datetime.now().isoformat()
    }

def initialize_application():
    """Initialise tous les composants de l'application"""
    
    print("🚀 Initialisation de la plateforme Oracle AI")
    
    # Vérifier Oracle Client
    oracle_available = check_oracle_client()
    
    # Initialiser le LLM Engine
    try:
        from src.llm_engine import LLMEngine
        llm_engine = LLMEngine(model="llama2")
        print("✅ LLM Engine initialisé")
    except Exception as e:
        print(f"❌ Erreur LLM: {e}")
        print("🔄 Utilisation du mode simulation...")
        # Si llama2 n'est pas disponible, utilisez 'simulate'
        llm_engine = LLMEngine(model="simulate")
    
    # Initialiser l'extracteur de données
    real_data = False
    extractor = None
    
    if oracle_available:
        try:
            from config import Config
            from src.data_extractor import OracleExtractor
            
            print(f"🔗 Connexion à Oracle: {Config.ORACLE_DSN}")
            
            extractor = OracleExtractor(
                username=Config.ORACLE_USER,
                password=Config.ORACLE_PASSWORD,
                dsn=Config.ORACLE_DSN
            )
            
            if extractor.test_connection():
                print("✅ Connexion Oracle établie")
                real_data = True
            else:
                print("⚠️  Connexion Oracle échouée, mode démonstration")
                real_data = False
        except Exception as e:
            print(f"❌ Erreur connexion Oracle: {e}")
            real_data = False
    
    # Initialiser l'auditeur de sécurité
    from src.security_audit import SecurityAuditor
    auditor = SecurityAuditor(llm_engine=llm_engine)
    print("✅ Security Auditor initialisé")
    
    # Stocker dans la session Streamlit
    st.session_state.llm_engine = llm_engine
    st.session_state.auditor = auditor
    st.session_state.extractor = extractor
    st.session_state.real_data = real_data
    
    # Créer un rapport d'audit de démonstration
    if not hasattr(st.session_state, 'audit_report'):
        # Utiliser la nouvelle méthode generate_sample_report
        st.session_state.audit_report = auditor.generate_sample_report()
        print("📋 Rapport d'audit de démonstration créé")
    
    # Créer des données de test
    if not hasattr(st.session_state, 'mock_data'):
        st.session_state.mock_data = create_mock_data()
    
    return {
        "llm_engine": llm_engine,
        "auditor": auditor,
        "extractor": extractor,
        "real_data": real_data
    }

def main():
    """Fonction principale pour Streamlit"""
    
    # Initialiser Streamlit
    st.set_page_config(
        page_title="Oracle AI Platform",
        page_icon="🔒",
        layout="wide"
    )
    
    # Initialiser l'application une seule fois
    if 'app_initialized' not in st.session_state:
        print("🔧 Initialisation de l'application...")
        initialize_application()
        st.session_state.app_initialized = True
    
    # Créer la barre latérale
    with st.sidebar:
        st.title("🔒 Oracle AI Platform")
        
        menu = st.radio(
            "Navigation",
            ["Accueil", "Sécurité", "Performance", "Sauvegardes", "Chatbot"]
        )
        
        st.divider()
        
        # Statut global
        st.metric("Score Sécurité", "85/100", delta="+2")
        st.metric("Requêtes Lentes", "12", delta="-3")
        st.metric("Dernier Backup", datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        st.divider()
        
        # Quick actions
        st.subheader("Actions Rapides")
        if st.button("🔍 Lancer Audit", use_container_width=True):
            st.session_state.run_audit = True
            st.success("Audit lancé avec succès!")
            
        if st.button("⚡ Analyser Performances", use_container_width=True):
            st.session_state.analyze_performance = True
            st.info("Analyse des performances en cours...")
    
    # Afficher la page correspondante
    if menu == "Accueil":
        show_home_page()
    elif menu == "Sécurité":
        show_security_page()
    elif menu == "Performance":
        show_performance_page()
    elif menu == "Sauvegardes":
        show_backup_page()
    elif menu == "Chatbot":
        show_chatbot_page()
    
    # Footer
    st.sidebar.divider()
    st.sidebar.caption("Oracle AI Platform v1.0.0")

def show_home_page():
    """Page d'accueil"""
    st.title("Tableau de Bord Oracle AI")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Base de Données", "PROD-DB", "En ligne")
    
    with col2:
        st.metric("Alertes Actives", "3", "2 critiques")
    
    with col3:
        st.metric("Performance", "92%", "-3%")
    
    with col4:
        st.metric("Espace Disque", "78%", "⚠️")
    
    # Graphiques simples
    st.subheader("📈 Vue d'ensemble")
    
    # Données de démonstration
    col1, col2 = st.columns(2)
    
    with col1:
        data = pd.DataFrame({
            'Ressource': ['CPU', 'Mémoire', 'IO', 'Réseau'],
            'Utilisation (%)': [75, 65, 42, 28]
        })
        st.bar_chart(data.set_index('Ressource'))
    
    with col2:
        hours = list(range(24))
        query_counts = [100 + i*20 for i in hours]
        query_data = pd.DataFrame({'Heure': hours, 'Requêtes': query_counts})
        st.line_chart(query_data.set_index('Heure'))
    
    # Alertes critiques
    st.subheader("🚨 Alertes Récentes")
    
    alerts = [
        {"type": "Sécurité", "message": "Tentative de connexion suspecte détectée", "time": "Il y a 5 min"},
        {"type": "Performance", "message": "Requête SQL bloquante détectée", "time": "Il y a 12 min"},
        {"type": "Stockage", "message": "Espace tablespace SYSTEM à 95%", "time": "Il y a 1 heure"}
    ]
    
    for alert in alerts:
        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                if alert["type"] == "Sécurité":
                    st.error(f"🔒 {alert['type']}: {alert['message']}")
                elif alert["type"] == "Performance":
                    st.warning(f"⚡ {alert['type']}: {alert['message']}")
                else:
                    st.info(f"💾 {alert['type']}: {alert['message']}")
            with col_b:
                st.caption(alert["time"])

def show_security_page():
    """Page sécurité"""
    st.title("🔒 Audit de Sécurité")
    
    # Récupérer le rapport d'audit
    audit_report = st.session_state.get('audit_report', {})
    
    # Score et jauge
    col1, col2 = st.columns([2, 1])
    
    with col1:
        score = audit_report.get('score', 85)
        st.subheader(f"Score de Sécurité: {score}/100")
        
        # Barre de progression colorée
        if score >= 80:
            st.progress(score/100, text="Excellent")
            st.success("✅ Sécurité optimale")
        elif score >= 60:
            st.progress(score/100, text="Bon")
            st.warning("⚠️ Améliorations possibles")
        else:
            st.progress(score/100, text="Critique")
            st.error("❌ Action immédiate requise")
    
    with col2:
        summary = audit_report.get('summary', {})
        st.metric("Risques Totaux", summary.get('total', 0))
        st.metric("Critiques", summary.get('critical', 0))
        st.metric("Recommandations", len(audit_report.get('recommendations', [])))
    
    # Liste des risques
    st.subheader("📋 Risques Identifiés")
    
    risks = audit_report.get('risks', [])
    if risks:
        for i, risk in enumerate(risks, 1):
            with st.expander(f"{i}. [{risk.get('severity', 'MEDIUM')}] {risk.get('type', '')}"):
                st.write(f"**Description**: {risk.get('description', '')}")
                if risk.get('details'):
                    st.write(f"**Détails**: {risk.get('details', '')}")
                st.write(f"**Recommandation**: {risk.get('recommendation', '')}")
    else:
        st.info("✅ Aucun risque identifié")
    
    # Recommandations
    st.subheader("✅ Recommandations")
    recommendations = audit_report.get('recommendations', [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            col_a, col_b = st.columns([1, 4])
            with col_a:
                priority = rec.get('priority', 'MEDIUM')
                if priority == 'CRITICAL':
                    st.error("🔴 Critique")
                elif priority == 'HIGH':
                    st.warning("🟠 Haute")
                elif priority == 'MEDIUM':
                    st.warning("🟡 Moyenne")
                else:
                    st.info("🟢 Basse")
            with col_b:
                st.write(f"**{i}.** {rec.get('action', '')}")
    else:
        st.success("✅ Toutes les recommandations ont été appliquées")

def show_performance_page():
    """Page de performance"""
    st.title("⚡ Analyse de Performance")
    
    # Métriques de performance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Temps de réponse moyen", "125ms", "-15ms")
    
    with col2:
        st.metric("Throughput", "1,250 req/s", "+45")
    
    with col3:
        st.metric("Taux d'erreur", "0.2%", "stable")
    
    # Top 10 des requêtes lentes
    st.subheader("🐌 Top 10 Requêtes Lentes")
    
    mock_data = st.session_state.get('mock_data', {})
    perf_metrics = mock_data.get('performance_metrics', {})
    slow_queries = perf_metrics.get('slow_queries', pd.DataFrame())
    
    if not slow_queries.empty:
        st.dataframe(slow_queries, use_container_width=True)
    else:
        st.info("Aucune requête lente détectée")
    
    # Bouton d'analyse
    if st.button("🔍 Analyser une requête lente", type="primary"):
        with st.spinner("Analyse en cours..."):
            # Simuler une analyse
            analysis_result = {
                "problèmes": ["Scan complet de table", "Index manquant"],
                "recommandations": [
                    "Ajouter un index sur la colonne de jointure",
                    "Réécrire la requête pour éviter le SELECT *"
                ],
                "gain_estimé": "70-80%"
            }
            
            st.success("✅ Analyse terminée!")
            st.write("**Problèmes identifiés:**")
            for pb in analysis_result["problèmes"]:
                st.write(f"- {pb}")
            
            st.write("**Recommandations:**")
            for rec in analysis_result["recommandations"]:
                st.write(f"- {rec}")
            
            st.write(f"**Gain estimé:** {analysis_result['gain_estimé']}")

def show_backup_page():
    """Page de sauvegardes"""
    st.title("💾 Gestion des Sauvegardes")
    
    # Statut des sauvegardes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Dernière sauvegarde", datetime.now().strftime("%Y-%m-%d %H:%M"), "Réussie")
    
    with col2:
        st.metric("Prochaine sauvegarde", "Dans 4h", "Planifiée")
    
    with col3:
        st.metric("Espace backup", "245 Go", "+15 Go")
    
    # Recommandation de stratégie
    st.subheader("🤖 Recommandation de Stratégie")
    
    with st.form("backup_strategy"):
        st.write("Configurez vos besoins:")
        
        rpo = st.selectbox("RPO (Perte de données max):", 
                          ["15 min", "1 heure", "4 heures", "24 heures"])
        rto = st.selectbox("RTO (Temps de restauration max):",
                          ["30 min", "1 heure", "4 heures", "12 heures"])
        budget = st.selectbox("Budget:", ["Faible", "Moyen", "Élevé"])
        
        if st.form_submit_button("Générer la stratégie"):
            with st.spinner("Génération de la stratégie optimale..."):
                strategy = generate_backup_strategy(rpo, rto, budget)
                
                st.success("✅ Stratégie générée!")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**Stratégie recommandée:**")
                    st.write(f"- Type: {strategy['type']}")
                    st.write(f"- Fréquence: {strategy['frequency']}")
                    st.write(f"- Rétention: {strategy['retention']}")
                
                with col_b:
                    st.write("**Script RMAN:**")
                    st.code(strategy['rman_script'], language="sql")

def generate_backup_strategy(rpo, rto, budget):
    """Génère une stratégie de sauvegarde"""
    strategies = {
        ("15 min", "30 min", "Élevé"): {
            "type": "Archivelog + Flashback",
            "frequency": "Toutes les 15 min",
            "retention": "7 jours",
            "rman_script": """RUN {
  ALLOCATE CHANNEL ch1 TYPE DISK;
  BACKUP DATABASE PLUS ARCHIVELOG;
  BACKUP CURRENT CONTROLFILE;
  RELEASE CHANNEL ch1;
}"""
        },
        ("1 heure", "1 heure", "Moyen"): {
            "type": "Incrémentale + Archivage",
            "frequency": "Quotidienne (incrémentale) + Hebdomadaire (complète)",
            "retention": "30 jours",
            "rman_script": """RUN {
  ALLOCATE CHANNEL ch1 TYPE DISK;
  BACKUP INCREMENTAL LEVEL 1 DATABASE;
  BACKUP ARCHIVELOG ALL;
  RELEASE CHANNEL ch1;
}"""
        },
        ("24 heures", "12 heures", "Faible"): {
            "type": "Complète hebdomadaire",
            "frequency": "Hebdomadaire",
            "retention": "90 jours",
            "rman_script": """RUN {
  ALLOCATE CHANNEL ch1 TYPE DISK;
  BACKUP DATABASE;
  RELEASE CHANNEL ch1;
}"""
        }
    }
    
    # Retourner la stratégie correspondante ou par défaut
    key = (rpo, rto, budget)
    if key in strategies:
        return strategies[key]
    else:
        return {
            "type": "Complète + Archivage",
            "frequency": "Quotidienne",
            "retention": "30 jours",
            "rman_script": """RUN {
  ALLOCATE CHANNEL ch1 TYPE DISK;
  BACKUP DATABASE PLUS ARCHIVELOG;
  RELEASE CHANNEL ch1;
}"""
        }

def show_chatbot_page():
    """Interface du chatbot"""
    st.title("🤖 Assistant Oracle IA")
    
    # Initialiser l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bonjour! Je suis votre assistant Oracle IA. Comment puis-je vous aider aujourd'hui?"}
        ]
    
    # Afficher l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input utilisateur
    if prompt := st.chat_input("Posez votre question sur Oracle..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        
        # Afficher le message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Générer la réponse
        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                response = generate_response(prompt)
                st.markdown(response)
        
        # Ajouter la réponse à l'historique
        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

def generate_response(query: str) -> str:
    """Génère une réponse via les modules appropriés"""
    query_lower = query.lower()
    
    # Réponses pré-définies basées sur le type de question
    if any(word in query_lower for word in ["lent", "performance", "optimiser", "rapide"]):
        return get_performance_response()
    
    elif any(word in query_lower for word in ["sécurité", "risque", "audit", "mot de passe"]):
        return get_security_response()
    
    elif any(word in query_lower for word in ["sauvegarde", "backup", "rman", "restaurer"]):
        return get_backup_response()
    
    elif any(word in query_lower for word in ["index", "table", "requête", "sql"]):
        return get_sql_response()
    
    elif any(word in query_lower for word in ["bonjour", "hello", "salut", "aide"]):
        return "Bonjour! Je suis votre assistant Oracle IA. Je peux vous aider avec:\n- Optimisation des performances\n- Audit de sécurité\n- Gestion des sauvegardes\n- Analyse de requêtes SQL\n\nQue souhaitez-vous savoir?"
    
    else:
        return f"Je suis votre assistant Oracle IA. Pour mieux vous aider avec votre question sur '{query}', pourriez-vous préciser si cela concerne:\n1. Les performances\n2. La sécurité\n3. Les sauvegardes\n4. Une requête SQL spécifique"

def get_performance_response():
    """Réponses pour les questions de performance"""
    responses = [
        "Pour optimiser les performances Oracle:\n1. Vérifiez les requêtes lentes via V$SQLSTAT\n2. Ajoutez des indexes sur les colonnes fréquemment interrogées\n3. Utilisez EXPLAIN PLAN pour analyser l'exécution\n4. Considérez le partitionnement pour les grandes tables",
        "Si votre requête est lente, vérifiez:\n- Les scans complets de table\n- Les jointures non indexées\n- Le manque de statistiques à jour\n- La fragmentation des indexes",
    ]
    import random
    return random.choice(responses)

def get_security_response():
    """Réponses pour les questions de sécurité"""
    responses = [
        "Pour renforcer la sécurité Oracle:\n1. Désactivez les comptes inutilisés\n2. Utilisez des profils de mot de passe forts\n3. Activez l'audit sur les actions sensibles\n4. Appliquez le principe du moindre privilège",
    ]
    import random
    return random.choice(responses)

def get_backup_response():
    """Réponses pour les questions de sauvegarde"""
    responses = [
        "Stratégie de sauvegarde recommandée:\n- Sauvegarde complète hebdomadaire\n- Sauvegarde incrémentale quotidienne\n- Archivage des logs toutes les heures\n- Test de restauration mensuel",
    ]
    import random
    return random.choice(responses)

def get_sql_response():
    """Réponses pour les questions SQL"""
    responses = [
        "Pour optimiser une requête SQL:\n1. Utilisez EXPLAIN PLAN\n2. Ajoutez des indexes appropriés\n3. Évitez SELECT *\n4. Utilisez des jointures internes quand possible",
    ]
    import random
    return random.choice(responses)

if __name__ == "__main__":
    # Lancer l'application
    main()