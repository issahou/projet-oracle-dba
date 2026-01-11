# src/dashboard_phi.py - VERSION COMPLÈTE CORRIGÉE
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import json

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class OracleAIDashboardPhi:
    def __init__(self):
        st.set_page_config(
            page_title="Oracle AI Platform ",
            page_icon="⚡",
            layout="wide"
        )
        
        # Initialisation
        self.llm_engine = None
        self.auditor = None
        self.mock_data = None
        self.model_name = "simulate"
        
        # Démarrer l'initialisation
        self._init_components()
    
    def _init_components(self):
        """Initialise les composants pour Phi"""
        if 'phi_initialized' not in st.session_state:
            print("🚀 Initialisation pour Phi...")
            
            # 1. Essayer d'importer et initialiser Phi
            try:
                from src.llm_engine_phi import LLMEnginePhi
                self.llm_engine = LLMEnginePhi(model="phi:latest")
                
                # Tester la connexion
                success, message = self.llm_engine.test_connection()
                print(f"🔗 {message}")
                
                if success:
                    self.model_name = "phi:latest"
                    print("✅ Phi Engine initialisé")
                else:
                    print("⚠️ Utilisation du mode simulation")
                    self.model_name = "simulate"
                    self.llm_engine = None  # Pas de simulateur, utiliser LLM réel
                    
            except Exception as e:
                print(f"❌ Erreur Phi: {e}")
                self.model_name = "simulate"
                self.llm_engine = None
            
            # 2. Initialiser l'auditeur avec le bon engine
            try:
                from src.security_audit import SecurityAuditor
                self.auditor = SecurityAuditor(llm_engine=self.llm_engine)
                print("✅ Security Auditor initialisé")
            except Exception as e:
                print(f"⚠️ Audit simulation: {e}")
                self.auditor = None
            
            # 3. Créer des données mock
            self.mock_data = self._create_phi_mock_data()
            
            # 4. Stocker dans session
            st.session_state.llm_engine = self.llm_engine
            st.session_state.auditor = self.auditor
            st.session_state.mock_data = self.mock_data
            st.session_state.model_name = self.model_name
            st.session_state.phi_initialized = True
            
            print("🎉 Initialisation Phi terminée")
    
    def _create_phi_mock_data(self):
        """Crée des données mock détaillées"""
        return {
            'audit_logs': pd.DataFrame({
                'USERID': ['SYS', 'SYSTEM', 'HR_ADMIN', 'FINANCE', 'DBA_USER'],
                'TIMESTAMP': [datetime.now() - timedelta(hours=i) for i in range(5)],
                'ACTION': ['LOGON', 'SELECT', 'UPDATE', 'DELETE', 'CREATE TABLE'],
                'RETURNCODE': [0, 0, 0, 0, 1017],
                'OBJECT_NAME': ['V$DATABASE', 'EMPLOYEES', 'SALARIES', 'TRANSACTIONS', 'AUDIT_TABLE'],
                'DETAILS': ['Connexion administrateur', 'Lecture table employees', 'Mise à jour salaires', 'Suppression anciennes transactions', 'Échec création - privilèges insuffisants']
            }),
            'performance_metrics': {
                'slow_queries': pd.DataFrame({
                    'SQL_ID': ['8fktjq7s4mz5a', '3ghs82kdj45sn', '7fjsk93md84la', '1ksjd94md75zn', '5gjsm83ld94ka'],
                    'SQL_TEXT': [
                        'SELECT * FROM employees WHERE department_id = :dept AND hire_date > :date',
                        'SELECT e.*, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id',
                        'UPDATE salaries SET amount = amount * 1.05 WHERE employee_id IN (SELECT employee_id FROM employees WHERE status = "ACTIVE")',
                        'DELETE FROM logs WHERE log_date < ADD_MONTHS(SYSDATE, -12)',
                        'SELECT COUNT(*), department_id FROM employees GROUP BY department_id HAVING COUNT(*) > 100'
                    ],
                    'ELAPSED_TIME_MS': [4500, 3200, 2800, 5100, 8900],
                    'CPU_PERCENT': [85, 72, 68, 91, 95],
                    'EXECUTIONS': [1500, 850, 200, 50, 25],
                    'PROBLEM': ['Full table scan', 'Join inefficace', 'Subquery coûteuse', 'Pas d\'index date', 'Group by lourd']
                })
            },
            'security_config': {
                'users': pd.DataFrame({
                    'USERNAME': ['SYS', 'SYSTEM', 'HR', 'FINANCE', 'APP_USER', 'REPORT_USER'],
                    'ACCOUNT_STATUS': ['OPEN', 'OPEN', 'EXPIRED', 'LOCKED', 'OPEN', 'EXPIRED'],
                    'PROFILE': ['DEFAULT', 'DEFAULT', 'HR_PROFILE', 'FINANCE_PROFILE', 'APP_PROFILE', 'DEFAULT'],
                    'LAST_LOGIN': ['2024-01-10', '2024-01-09', '2023-12-15', '2023-11-20', '2024-01-11', '2023-10-05'],
                    'PRIVILEGES': ['SYSDBA', 'DBA', 'SELECT ANY TABLE', 'INSERT, UPDATE', 'CONNECT', 'SELECT']
                })
            }
        }
    
    def setup_sidebar(self):
        """Barre latérale optimisée"""
        with st.sidebar:
            st.title("⚡ Oracle AI")
            
            menu = st.radio(
                "Menu",
                ["🏠 Accueil", "🔒 Sécurité", "⚡ Performance", "💾 Backup", "🤖 Chat"]
            )
            
            st.divider()
            
            # Statut
            st.subheader("Status")
            col1, col2 = st.columns(2)
            with col1:
                icon = "🟢" if self.model_name == "phi:latest" else "🟡"
                st.metric("AI", f"{icon} {self.model_name}")
            with col2:
                if self.llm_engine and hasattr(self.llm_engine, 'test_connection'):
                    success, msg = self.llm_engine.test_connection()
                    status = "✅ Connecté" if success else "❌ Erreur"
                    st.metric("Connexion", status)
            
            # Actions
            st.divider()
            st.subheader("Actions")
            
            if st.button("🔄 Rafraîchir IA", use_container_width=True):
                st.session_state.refresh_ai = True
            
            if st.button("🧪 Tester Phi", use_container_width=True):
                st.session_state.test_phi_detailed = True
            
            if st.button("📊 Logs debug", use_container_width=True):
                st.session_state.show_debug = True
        
        # Convertir le menu
        menu_map = {
            "🏠 Accueil": "home",
            "🔒 Sécurité": "security", 
            "⚡ Performance": "performance",
            "💾 Backup": "backup",
            "🤖 Chat": "chat"
        }
        return menu_map.get(menu, "home")
    
    def home_page(self):
        """Page d'accueil avec détails"""
        st.title("⚡ Oracle AI Platform")
        st.caption(f"Powered by {self.model_name.upper()} - Réponses IA authentiques")
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "🟢 RÉEL" if self.model_name == "phi:latest" else "🟡 SIMULATION"
            st.metric("Statut IA", status)
        
        with col2:
            st.metric("Requêtes", "12", "+2")
        
        with col3:
            st.metric("Sécurité", "85%", "⚠️")
        
        with col4:
            st.metric("Réponse", "<2s", "⚡")
        
        # Test Phi détaillé
        if st.session_state.get('test_phi_detailed'):
            self._test_phi_detailed()
            st.session_state.test_phi_detailed = False
        
        # Debug info
        if st.session_state.get('show_debug'):
            with st.expander("🔧 Debug Information"):
                st.write(f"**Modèle:** {self.model_name}")
                st.write(f"**Engine type:** {type(self.llm_engine).__name__ if self.llm_engine else 'None'}")
                if self.llm_engine and hasattr(self.llm_engine, 'model'):
                    st.write(f"**Model attribut:** {self.llm_engine.model}")
                
                # Test direct
                if st.button("Tester generate()"):
                    with st.spinner("Test en cours..."):
                        try:
                            if self.llm_engine:
                                response = self.llm_engine.generate(
                                    "chatbot_general",
                                    variables={"query": "Test technique Oracle", "history": ""},
                                    max_tokens=200
                                )
                                st.code(response[:500], language="text")
                            else:
                                st.error("LLM Engine non disponible")
                        except Exception as e:
                            st.error(f"Erreur: {e}")
            
            st.session_state.show_debug = False
        
        # Section principale
        st.subheader("🎯 Capacités de l'Assistant")
        
        capabilities = {
            "🔍 Audit Sécurité": "Analyse complète des configurations de sécurité Oracle avec recommandations détaillées",
            "⚡ Optimisation SQL": "Diagnostic approfondi des requêtes lentes avec plans d'optimisation",
            "💾 Stratégie Backup": "Plans de sauvegarde RMAN personnalisés avec scripts exécutables",
            "📊 Monitoring": "Outils de surveillance des performances en temps réel",
            "🛠️ Dépannage": "Solutions techniques pour les problèmes courants Oracle"
        }
        
        for cap, desc in capabilities.items():
            with st.expander(cap):
                st.write(desc)
    
    def _test_phi_detailed(self):
        """Test détaillé de Phi"""
        st.subheader("🧪 Test Complet de Phi")
        
        if not self.llm_engine:
            st.error("❌ LLM Engine non disponible - impossible de tester")
            return
        
        with st.spinner("Test des différentes fonctionnalités..."):
            # Test 1: Chat général
            st.write("**1. Test Chat Général:**")
            try:
                response1 = self.llm_engine.chat_response(
                    "Comment créer un index efficace sur Oracle?",
                    ""
                )
                with st.expander("Voir réponse chat"):
                    st.write(response1[:1000] + "..." if len(response1) > 1000 else response1)
            except Exception as e:
                st.error(f"Erreur chat: {e}")
            
            # Test 2: Analyse sécurité
            st.write("**2. Test Analyse Sécurité:**")
            try:
                test_config = {"users": 5, "audit": False, "profiles": "DEFAULT"}
                response2 = self.llm_engine.assess_security(test_config)
                if isinstance(response2, dict):
                    st.write(f"Score: {response2.get('score', 'N/A')}")
                    st.write(f"Risques: {len(response2.get('risks', []))}")
                else:
                    st.write(f"Réponse: {str(response2)[:200]}...")
            except Exception as e:
                st.error(f"Erreur sécurité: {e}")
            
            # Test 3: Backup
            st.write("**3. Test Stratégie Backup:**")
            try:
                response3 = self.llm_engine.get_backup_strategy({
                    "rpo": "1h",
                    "rto": "30min",
                    "data_size": "500GB"
                })
                if isinstance(response3, dict):
                    st.write(f"Type: {response3.get('strategy', {}).get('type', 'N/A')}")
                else:
                    st.write(f"Réponse: {str(response3)[:200]}...")
            except Exception as e:
                st.error(f"Erreur backup: {e}")
    
    def security_page(self):
        """Page sécurité avec interface améliorée"""
        st.title("🔒 Audit de Sécurité Détaillé")
        
        # Configuration
        with st.expander("⚙️ Configuration de l'Audit", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                scope = st.selectbox("Portée", ["Complet", "Utilisateurs", "Privilèges", "Audit"])
                depth = st.selectbox("Profondeur", ["Standard", "Approfondi", "Expert"])
            with col2:
                include_recommendations = st.checkbox("Inclure recommandations", True)
                include_scripts = st.checkbox("Inclure scripts SQL", True)
        
        # Bouton d'audit principal
        if st.button("🔍 Lancer l'audit complet", type="primary", use_container_width=True):
            self._run_detailed_security_audit(scope, depth, include_recommendations, include_scripts)
        
        # Afficher le rapport existant
        if 'detailed_audit_report' in st.session_state:
            self._display_detailed_security_report(st.session_state.detailed_audit_report)
    
    def _run_detailed_security_audit(self, scope, depth, include_recs, include_scripts):
        """Exécute un audit de sécurité détaillé"""
        with st.spinner("🔍 Analyse de sécurité en cours..."):
            try:
                # Utiliser les données mock comme configuration
                security_data = self.mock_data.get('security_config', {})
                
                if self.auditor:
                    # Générer un rapport via l'auditeur
                    report = self.auditor.audit_database(security_data)
                    
                    # Améliorer le rapport avec LLM si disponible
                    if self.llm_engine:
                        report = self._enhance_security_report(report, security_data)
                    
                    st.session_state.detailed_audit_report = report
                    
                    # Afficher les résultats
                    self._display_audit_results(report)
                    
                else:
                    st.error("Auditeur non disponible")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'audit: {str(e)}")
                import traceback
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())
    
    def _enhance_security_report(self, report, security_data):
        """Améliore le rapport avec analyse LLM"""
        if not self.llm_engine:
            return report
        
        try:
            # Générer analyse supplémentaire avec LLM
            llm_response = self.llm_engine.assess_security(security_data)
            
            if isinstance(llm_response, dict):
                # Fusionner les risques LLM avec le rapport existant
                report['llm_enhanced'] = True
                if 'risks' in llm_response:
                    report['risks'].extend(llm_response['risks'])
                if 'recommendations' in llm_response:
                    report['recommendations'].extend(llm_response['recommendations'])
                
                # Recalculer le score
                report['score'] = self.auditor._calculate_score(report['risks']) if self.auditor else report['score']
                report['summary'] = self.auditor._update_summary(report['risks']) if self.auditor else report['summary']
            
        except Exception as e:
            print(f"Erreur enhancement LLM: {e}")
        
        return report
    
    def _display_audit_results(self, report):
        """Affiche les résultats de l'audit"""
        score = report.get('score', 0)
        
        # Jauge de score
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Score Sécurité", 'font': {'size': 24}},
            delta={'reference': 70, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': 'red'},
                    {'range': [50, 80], 'color': 'yellow'},
                    {'range': [80, 100], 'color': 'green'}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': score}
            }
        ))
        
        fig.update_layout(height=300, margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
        
        # Détails des risques
        st.subheader("📋 Détails des Risques")
        risks = report.get('risks', [])
        
        if risks:
            for i, risk in enumerate(risks, 1):
                severity = risk.get('severity', 'MEDIUM')
                severity_color = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠', 
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(severity, '⚪')
                
                with st.expander(f"{severity_color} {i}. {risk.get('type', 'Risque')} - {severity}", expanded=i==1):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Description:** {risk.get('description', '')}")
                        if risk.get('details'):
                            st.write(f"**Détails techniques:** {risk.get('details', '')}")
                    with col2:
                        if severity == 'CRITICAL':
                            st.error("ACTION IMMÉDIATE")
                        elif severity == 'HIGH':
                            st.warning("ACTION RAPIDE")
                        elif severity == 'MEDIUM':
                            st.info("PLANIFIER")
                        else:
                            st.success("SUIVI")
                    
                    st.write(f"**✅ Recommandation:** {risk.get('recommendation', '')}")
                    
                    # Bouton pour générer des scripts
                    if st.button(f"Générer script pour ce risque", key=f"script_{i}"):
                        script = self._generate_security_script(risk)
                        st.code(script, language="sql")
        else:
            st.success("🎉 Aucun risque identifié!")
    
    def _display_detailed_security_report(self, report):
        """Affiche le rapport de sécurité détaillé"""
        self._display_audit_results(report)
    
    def _generate_security_script(self, risk):
        """Génère un script SQL pour corriger un risque"""
        risk_type = risk.get('type', '').upper()
        
        scripts = {
            'AUDIT_DISABLED': """-- Activer l'audit Oracle
ALTER SYSTEM SET AUDIT_TRAIL=DB SCOPE=SPFILE;
-- Redémarrer la base
SHUTDOWN IMMEDIATE;
STARTUP;
-- Configurer l'audit des actions sensibles
AUDIT SELECT ANY TABLE, UPDATE ANY TABLE, DELETE ANY TABLE BY ACCESS;
AUDIT CREATE SESSION WHENEVER NOT SUCCESSFUL;
-- Vérifier la configuration
SELECT * FROM DBA_AUDIT_TRAIL WHERE ROWNUM < 10;""",
            
            'WEAK_PASSWORD': """-- Créer un profil de sécurité fort
CREATE PROFILE secure_profile LIMIT
  FAILED_LOGIN_ATTEMPTS 5
  PASSWORD_LIFE_TIME 90
  PASSWORD_REUSE_TIME 365
  PASSWORD_REUSE_MAX 10
  PASSWORD_LOCK_TIME 1
  PASSWORD_GRACE_TIME 7;
  
-- Appliquer aux utilisateurs critiques
ALTER USER SYS PROFILE secure_profile;
ALTER USER SYSTEM PROFILE secure_profile;
ALTER USER DBSNMP PROFILE secure_profile;

-- Forcer le changement de mot de passe
ALTER USER SYS IDENTIFIED BY "N3w$tr0ngP@ssw0rd#2024";
ALTER USER SYSTEM IDENTIFIED BY "Syst3m$tr0ngP@ss#2024";""",
            
            'DEFAULT_ACCOUNT': """-- Désactiver les comptes par défaut inutilisés
ALTER USER OUTLN ACCOUNT LOCK;
ALTER USER MGMT_VIEW ACCOUNT LOCK;
ALTER USER ORACLE_OCM ACCOUNT LOCK;

-- Changer les mots de passe des comptes utilisés
ALTER USER SYS IDENTIFIED BY [mot_de_passe_fort];
ALTER USER SYSTEM IDENTIFIED BY [mot_de_passe_fort];

-- Vérifier les comptes actifs
SELECT username, account_status, created 
FROM dba_users 
WHERE account_status != 'LOCKED' 
ORDER BY created DESC;"""
        }
        
        return scripts.get(risk_type, f"-- Script pour {risk_type}\n-- {risk.get('recommendation', '')}")
    
    def performance_page(self):
        """Page performance améliorée"""
        st.title("⚡ Analyse de Performance Avancée")
        
        # Section d'analyse interactive
        st.subheader("📊 Analyse Interactive des Requêtes")
        
        # Afficher les requêtes lentes
        metrics = self.mock_data.get('performance_metrics', {})
        slow_queries = metrics.get('slow_queries', pd.DataFrame())
        
        if not slow_queries.empty:
            # Sélection de requête
            selected_idx = st.selectbox(
                "Sélectionnez une requête à analyser:",
                range(len(slow_queries)),
                format_func=lambda i: f"SQL_{slow_queries.iloc[i]['SQL_ID'][:8]} - {slow_queries.iloc[i]['ELAPSED_TIME_MS']}ms - {slow_queries.iloc[i]['PROBLEM']}"
            )
            
            selected_query = slow_queries.iloc[selected_idx]
            
            # Détails de la requête
            with st.expander("🔍 Détails de la requête sélectionnée", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Temps", f"{selected_query['ELAPSED_TIME_MS']}ms")
                with col2:
                    st.metric("CPU", f"{selected_query['CPU_PERCENT']}%")
                with col3:
                    st.metric("Exécutions", selected_query['EXECUTIONS'])
                
                st.code(selected_query['SQL_TEXT'], language="sql")
                st.caption(f"**Problème identifié:** {selected_query['PROBLEM']}")
            
            # Bouton d'analyse IA
            if st.button("🔍 Analyser avec IA avancée", type="primary"):
                self._analyze_query_advanced(selected_query)
        
        # Section de monitoring
        st.subheader("📈 Monitoring en Temps Réel")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temps réponse moyen", "125ms", "-15ms", delta_color="inverse")
        with col2:
            st.metric("Requêtes actives", "8", "+2")
        with col3:
            st.metric("CPU Database", "78%", "+5%")
    
    def _analyze_query_advanced(self, query_data):
        """Analyse avancée d'une requête"""
        with st.spinner("🧠 Analyse IA approfondie en cours..."):
            try:
                if self.llm_engine:
                    # Créer un plan d'exécution simulé détaillé
                    exec_plan = f"""
PLAN D'EXÉCUTION DÉTAILLÉ
-----------------------------------------------------------------------------------------------------------
| Id  | Operation                    | Name            | Rows  | Bytes | TempSpc| Cost (%CPU)| Time     |
-----------------------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT             |                 |   100 | 10500 |        |  1024 (100)| 00:00:01 |
|*  1 |  HASH JOIN                   |                 |   100 | 10500 |    16M|   512  (50)| 00:00:01 |
|   2 |   TABLE ACCESS FULL          | DEPARTMENTS     |    10 |   700 |        |     3   (0)| 00:00:01 |
|*  3 |   TABLE ACCESS FULL          | EMPLOYEES       | 50000 |  3500K|        |   509  (49)| 00:00:01 |
-----------------------------------------------------------------------------------------------------------

PREDICATE INFORMATION:
1 - access("E"."DEPARTMENT_ID"="D"."DEPARTMENT_ID")
3 - filter("E"."STATUS"='ACTIVE')

STATISTICS:
- Full Table Scan sur EMPLOYEES (50,000 lignes)
- Hash Join coûteuse (16M de Temp Space)
- Pas d'index sur DEPARTMENT_ID ou STATUS
- Statistiques potentiellement obsolètes
"""
                    
                    # Analyser avec LLM
                    analysis = self.llm_engine.analyze_query(
                        sql_query=query_data['SQL_TEXT'],
                        execution_plan=exec_plan
                    )
                    
                    # Afficher les résultats
                    st.success("✅ Analyse complète terminée!")
                    
                    with st.expander("📋 Rapport d'optimisation complet", expanded=True):
                        if isinstance(analysis, str):
                            st.markdown(analysis)
                        else:
                            st.write(analysis)
                        
                        # Section d'exemples pratiques
                        st.subheader("💡 Exemples pratiques d'optimisation")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Index recommandés:**")
                            st.code("""-- Index composite pour la requête
CREATE INDEX idx_emp_perf ON employees(
    department_id, 
    status, 
    hire_date
) TABLESPACE users_idx 
  PCTFREE 10 
  INITRANS 2 
  PARALLEL 4;

-- Statistiques
EXEC DBMS_STATS.GATHER_TABLE_STATS(
    ownname => 'HR',
    tabname => 'EMPLOYEES',
    estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE,
    method_opt => 'FOR ALL COLUMNS SIZE AUTO'
);""", language="sql")
                        
                        with col2:
                            st.write("**Requête optimisée:**")
                            st.code("""-- Version optimisée avec hints
SELECT /*+ INDEX(e idx_emp_perf) LEADING(d) USE_NL(e) */
       e.employee_id,
       e.first_name || ' ' || e.last_name as full_name,
       d.department_name,
       e.salary,
       e.hire_date
FROM departments d
JOIN employees e ON d.department_id = e.department_id
WHERE e.status = 'ACTIVE'
AND e.hire_date > ADD_MONTHS(SYSDATE, -60)
ORDER BY e.hire_date DESC, e.salary DESC;""", language="sql")
                        
                        # Téléchargement des scripts
                        optimization_script = self._create_optimization_script(query_data)
                        st.download_button(
                            label="📥 Télécharger les scripts d'optimisation",
                            data=optimization_script,
                            file_name=f"optimisation_{query_data['SQL_ID']}.sql",
                            mime="text/sql"
                        )
                        
                else:
                    st.warning("Mode simulation - Analyse basique")
                    self._show_basic_analysis(query_data)
                    
            except Exception as e:
                st.error(f"❌ Erreur d'analyse: {str(e)}")
                import traceback
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())
    
    def _create_optimization_script(self, query_data):
        """Crée un script SQL complet d'optimisation"""
        return f"""-- Script d'optimisation pour: {query_data['SQL_ID']}
-- Généré par Oracle AI Platform
-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- ============================================================================
-- 1. ANALYSE INITIALE
-- ============================================================================
/*
Problème identifié: {query_data['PROBLEM']}
Temps d'exécution: {query_data['ELAPSED_TIME_MS']}ms
Utilisation CPU: {query_data['CPU_PERCENT']}%
Nombre d'exécutions: {query_data['EXECUTIONS']}
*/

-- Requête originale:
{query_data['SQL_TEXT']}

-- ============================================================================
-- 2. INDEXATION RECOMMANDÉE
-- ============================================================================

-- Index principal (adapter les noms de tables/colonnes)
CREATE INDEX idx_optim_perf ON votre_table(
    colonne_join,
    colonne_filtre,
    colonne_select
) TABLESPACE indx_ts
  PCTFREE 10
  INITRANS 2
  STORAGE (INITIAL 64K NEXT 64K)
  NOLOGGING
  PARALLEL 4;

COMMENT ON INDEX idx_optim_perf IS 'Index pour optimisation requête {query_data['SQL_ID'][:8]}';

-- ============================================================================
-- 3. STATISTIQUES
-- ============================================================================

-- Mettre à jour les statistiques
BEGIN
  DBMS_STATS.GATHER_TABLE_STATS(
    ownname          => 'VOTRE_SCHEMA',
    tabname          => 'VOTRE_TABLE',
    estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE,
    method_opt       => 'FOR ALL COLUMNS SIZE AUTO',
    degree           => DBMS_STATS.AUTO_DEGREE,
    cascade          => TRUE
  );
END;
/

-- ============================================================================
-- 4. REQUÊTE OPTIMISÉE
-- ============================================================================

-- Version optimisée avec hints
SELECT /*+ INDEX(t idx_optim_perf) */
       colonne1,
       colonne2,
       colonne3
FROM votre_table t
WHERE conditions_optimisees
ORDER BY colonne_ordre;

-- ============================================================================
-- 5. VÉRIFICATIONS POST-OPTIMISATION
-- ============================================================================

-- Vérifier l'utilisation de l'index
SELECT * FROM v$object_usage 
WHERE index_name = 'IDX_OPTIM_PERF';

-- Analyser le nouveau plan d'exécution
EXPLAIN PLAN FOR
SELECT /*+ INDEX(t idx_optim_perf) */ * 
FROM votre_table t 
WHERE conditions;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- ============================================================================
-- 6. MONITORING
-- ============================================================================

-- Script de monitoring
SELECT sql_id, elapsed_time/1000000 as seconds, executions
FROM v$sql 
WHERE sql_id = '{query_data['SQL_ID']}';

-- AWR Report (à exécuter sur la base)
-- @?/rdbms/admin/awrrpt.sql
"""
    
    def _show_basic_analysis(self, query_data):
        """Affiche une analyse basique sans LLM"""
        st.info("Analyse basique (sans LLM)")
        st.write(f"**Problème:** {query_data['PROBLEM']}")
        st.write(f"**Temps:** {query_data['ELAPSED_TIME_MS']}ms")
        st.write(f"**CPU:** {query_data['CPU_PERCENT']}%")
    
    def backup_page(self):
        """Page backup améliorée - CORRIGÉE"""
        st.title("💾 Stratégie de Sauvegarde Avancée")
        
        # Variables pour stocker les valeurs du formulaire
        if 'backup_form_submitted' not in st.session_state:
            st.session_state.backup_form_submitted = False
        
        # Configuration interactive SANS formulaire pour éviter l'erreur download_button
        st.subheader("⚙️ Configuration des Besoins")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rpo = st.selectbox(
                "RPO (Perte de données maximale)",
                ["15 minutes", "1 heure", "4 heures", "24 heures", "7 jours"],
                index=0
            )
            data_size = st.selectbox(
                "Taille des données",
                ["< 100GB", "100GB - 1TB", "1TB - 10TB", "> 10TB"],
                index=1
            )
        
        with col2:
            rto = st.selectbox(
                "RTO (Temps de restauration maximal)", 
                ["30 minutes", "1 heure", "4 heures", "12 heures", "24 heures"],
                index=0
            )
            criticality = st.select_slider(
                "Criticité des données",
                options=["FAIBLE", "MOYENNE", "HAUTE", "CRITIQUE"],
                value="HAUTE"
            )
        
        advanced = st.checkbox("Options avancées")
        storage_type = "ASM"
        compression = True
        encryption = True
        
        if advanced:
            col3, col4 = st.columns(2)
            with col3:
                storage_type = st.selectbox(
                    "Type de stockage",
                    ["ASM", "NFS", "SAN", "Cloud Object Storage", "Tape"]
                )
                compression = st.checkbox("Compression", True)
            with col4:
                encryption = st.checkbox("Chiffrement", True)
                monitoring = st.checkbox("Monitoring actif", True)
        
        # Bouton de génération EN DEHORS du formulaire
        if st.button("🎯 Générer la stratégie optimale", type="primary"):
            self._generate_advanced_backup_strategy(
                rpo, rto, data_size, criticality,
                storage_type,
                compression,
                encryption
            )
            st.session_state.backup_form_submitted = True
        
        # Afficher la dernière stratégie générée
        if 'last_backup_strategy' in st.session_state:
            self._display_backup_results(st.session_state.last_backup_strategy)
    
    def _generate_advanced_backup_strategy(self, rpo, rto, data_size, criticality, storage, compression, encryption):
        """Génère une stratégie de backup avancée"""
        with st.spinner("🧠 Calcul de la stratégie optimale..."):
            try:
                requirements = {
                    'rpo': rpo,
                    'rto': rto,
                    'data_size': data_size,
                    'criticality': criticality,
                    'storage': storage,
                    'compression': compression,
                    'encryption': encryption
                }
                
                if self.llm_engine:
                    # Utiliser le LLM pour générer la stratégie
                    strategy = self.llm_engine.get_backup_strategy(requirements)
                    st.session_state.last_backup_strategy = strategy
                else:
                    st.warning("Mode simulation - Stratégie par défaut")
                    self._show_default_backup_strategy(requirements)
                    
            except Exception as e:
                st.error(f"❌ Erreur génération stratégie: {str(e)}")
                import traceback
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())
    
    def _display_backup_results(self, strategy):
        """Affiche les résultats de la stratégie de backup"""
        if not isinstance(strategy, dict):
            st.error("Format de stratégie invalide")
            return
        
        st.success("✅ Stratégie générée avec succès!")
        
        # Résumé
        st.subheader("📋 Résumé de la Stratégie")
        
        strat_info = strategy.get('strategy', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Type", strat_info.get('type', 'N/A'))
            st.metric("Fréquence", strat_info.get('frequency', 'N/A'))
        
        with col2:
            st.metric("Rétention", f"{strat_info.get('retention_days', 0)} jours")
            st.metric("Stockage", strat_info.get('storage', 'N/A'))
        
        with col3:
            cost = strat_info.get('estimated_cost', 'N/A')
            st.metric("Coût estimé", f"{cost}€" if isinstance(cost, (int, float)) else cost)
            advantages = strat_info.get('advantages', '')
            adv_count = len(advantages.split(',')) if isinstance(advantages, str) else 0
            st.metric("Avantages", adv_count)
        
        # Script RMAN
        st.subheader("📜 Script RMAN Complet")
        
        rman_script = strategy.get('rman_script', '')
        if rman_script:
            st.code(rman_script, language="sql")
            
            # Boutons d'action EN DEHORS du formulaire
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="📥 Télécharger le script",
                    data=rman_script,
                    file_name=f"rman_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.rcv",
                    mime="text/plain",
                    key="download_rman_script"
                )
            with col2:
                if st.button("🔄 Tester la syntaxe", key="test_rman"):
                    st.info("Syntaxe RMAN valide (test simulé)")
            with col3:
                if st.button("📊 Planifier l'exécution", key="schedule_rman"):
                    st.info("Planification disponible dans Enterprise Manager")
        else:
            st.warning("Pas de script RMAN généré")
        
        # Étapes d'implémentation
        st.subheader("🛠️ Étapes d'Implémentation")
        
        steps = strategy.get('implementation_steps', [])
        if steps:
            for i, step in enumerate(steps, 1):
                st.write(f"{i}. {step}")
        else:
            st.info("Génération des étapes en cours...")
    
    def _show_default_backup_strategy(self, requirements):
        """Affiche une stratégie de backup par défaut"""
        default_strategy = {
            "strategy": {
                "type": "INCREMENTAL_LEVEL_1",
                "frequency": "HOURLY",
                "retention_days": 30,
                "storage": "ASM",
                "estimated_cost": 2500,
                "advantages": "RPO court, Restauration rapide, Impact minimal production",
                "limitations": "Nécessite ASM, Espace disque important"
            },
            "rman_script": f"""-- Stratégie de sauvegarde Oracle RMAN
-- Configuration pour: RPO={requirements['rpo']}, RTO={requirements['rto']}
-- Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RUN {{
  -- 1. CONFIGURATION
  CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF 30 DAYS;
  CONFIGURE CONTROLFILE AUTOBACKUP ON;
  CONFIGURE CONTROLFILE AUTOBACKUP FORMAT FOR DEVICE TYPE DISK TO '%F';
  CONFIGURE DEVICE TYPE DISK PARALLELISM 4;
  CONFIGURE CHANNEL DEVICE TYPE DISK FORMAT '/backup/orcl/%U';
  
  -- 2. SAUVEGARDE PRINCIPALE
  ALLOCATE CHANNEL ch1 TYPE DISK;
  ALLOCATE CHANNEL ch2 TYPE DISK;
  ALLOCATE CHANNEL ch3 TYPE DISK;
  ALLOCATE CHANNEL ch4 TYPE DISK;
  
  BACKUP AS COMPRESSED BACKUPSET
    INCREMENTAL LEVEL 1
    DATABASE
    PLUS ARCHIVELOG
    DELETE ALL INPUT
    TAG 'DAILY_INCR';
    
  -- 3. SAUVEGARDE DU CONTROLFILE
  BACKUP CURRENT CONTROLFILE;
  
  -- 4. SAUVEGARDE SPFILE
  BACKUP SPFILE;
  
  -- 5. VALIDATION
  BACKUP VALIDATE DATABASE ARCHIVELOG ALL;
  
  -- 6. RAPPORTS
  REPORT OBSOLETE;
  REPORT NEED BACKUP;
  LIST BACKUP SUMMARY;
  
  -- 7. NETTOYAGE
  DELETE NOPROMPT OBSOLETE;
  CROSSCHECK BACKUP;
  DELETE NOPROMPT EXPIRED BACKUP;
  
  RELEASE CHANNEL ch1;
  RELEASE CHANNEL ch2;
  RELEASE CHANNEL ch3;
  RELEASE CHANNEL ch4;
}}""",
            "implementation_steps": [
                "Étape 1: Vérifier l'espace disque: SELECT * FROM V$ASM_DISKGROUP;",
                "Étape 2: Configurer les paramètres: ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = 500G;",
                "Étape 3: Créer le script de planification: /u01/app/oracle/scripts/rman_backup.sh",
                "Étape 4: Tester la restauration complète sur environnement de test",
                "Étape 5: Configurer les alertes OEM pour les échecs de backup",
                "Étape 6: Documenter la procédure de restauration d'urgence"
            ]
        }
        
        st.session_state.last_backup_strategy = default_strategy
        self._display_backup_results(default_strategy)
    
    def chatbot_page(self):
        """Chatbot amélioré avec historique complet"""
        st.title("🤖 Assistant Oracle Expert")
        st.caption(f"Powered by {self.model_name.upper()} - Réponses IA authentiques")
        
        # Initialiser l'historique
        if "phi_chat_history" not in st.session_state:
            st.session_state.phi_chat_history = [
                {
                    "role": "assistant",
                    "content": f"""👋 Bonjour! Je suis votre expert Oracle IA ({self.model_name}).

**Mes spécialités:**
• 🔍 Audit de sécurité avancé
• ⚡ Optimisation SQL approfondie  
• 💾 Stratégies de sauvegarde RMAN
• 📊 Monitoring et performances
• 🛠️ Dépannage technique

**Exemples de questions:**
1. "Comment optimiser une requête avec full table scan?"
2. "Quelle stratégie de backup pour un RPO de 15min?"
3. "Comment auditer la sécurité de ma base Oracle?"
4. "Quels indexes créer pour améliorer les performances?"

Posez-moi votre question technique!"""
                }
            ]
        
        # Afficher l'historique complet
        for message in st.session_state.phi_chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Input utilisateur
        if prompt := st.chat_input("Votre question technique Oracle..."):
            # Ajouter question
            st.session_state.phi_chat_history.append({"role": "user", "content": prompt})
            
            # Afficher immédiatement
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Générer la réponse
            self._generate_detailed_chat_response(prompt)
        
        # Contrôles avancés
        with st.sidebar.expander("⚙️ Contrôles Chat"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Effacer historique", use_container_width=True):
                    st.session_state.phi_chat_history = [
                        {"role": "assistant", "content": "Historique effacé. Comment puis-je vous aider?"}
                    ]
                    st.rerun()
            with col2:
                if st.button("💾 Exporter chat", use_container_width=True):
                    self._export_chat_history()
            
            # Questions rapides
            st.write("**💡 Questions rapides:**")
            quick_questions = [
                "Optimisation requête lente",
                "Stratégie backup RPO 1h",
                "Audit sécurité complet",
                "Monitoring performances"
            ]
            
            for q in quick_questions:
                if st.button(q, key=f"quick_{q}", use_container_width=True):
                    st.session_state.phi_chat_history.append({"role": "user", "content": q})
                    self._generate_detailed_chat_response(q)
                    st.rerun()
    
    def _generate_detailed_chat_response(self, prompt):
        """Génère une réponse de chat détaillée"""
        with st.chat_message("assistant"):
            with st.spinner("💭 Analyse en cours..."):
                try:
                    # Construire l'historique
                    history = "\n".join([
                        f"{msg['role'].upper()}: {msg['content']}" 
                        for msg in st.session_state.phi_chat_history[-5:]
                    ])
                    
                    # Générer la réponse AVEC LLM
                    if self.llm_engine:
                        response = self.llm_engine.chat_response(prompt, history)
                        
                        # Nettoyer et formater
                        if response and len(response) > 50:
                            formatted_response = self._format_chat_response(response, prompt)
                            st.markdown(formatted_response)
                            st.session_state.phi_chat_history.append(
                                {"role": "assistant", "content": formatted_response}
                            )
                        else:
                            fallback = self._get_fallback_response(prompt)
                            st.markdown(fallback)
                            st.session_state.phi_chat_history.append(
                                {"role": "assistant", "content": fallback}
                            )
                    else:
                        # Pas de LLM disponible
                        error_msg = "⚠️ LLM non disponible. Démarrez Ollama avec 'ollama pull phi' puis 'ollama serve'"
                        st.error(error_msg)
                        st.session_state.phi_chat_history.append(
                            {"role": "assistant", "content": error_msg}
                        )
                        
                except Exception as e:
                    error_msg = f"⚠️ Erreur de génération:\n```\n{str(e)[:200]}\n```"
                    st.error(error_msg)
                    st.session_state.phi_chat_history.append(
                        {"role": "assistant", "content": error_msg}
                    )
    
    def _format_chat_response(self, response, prompt):
        """Formate la réponse du chat pour une meilleure lisibilité"""
        # Retourner la réponse brute du LLM sans modification
        return response
    
    def _get_fallback_response(self, prompt):
        """Retourne une réponse de secours"""
        return f"""⚠️ Réponse limitée (LLM non disponible).

**Votre question:** {prompt}

**Suggestions:**
1. Vérifiez qu'Ollama est en cours d'exécution
2. Installez le modèle Phi: `ollama pull phi`
3. Redémarrez l'application

Pour des réponses complètes, assurez-vous que le LLM est correctement configuré."""
    
    def _export_chat_history(self):
        """Exporte l'historique du chat"""
        if 'phi_chat_history' in st.session_state:
            history_text = "\n\n".join([
                f"{'='*50}\n{msg['role'].upper()}\n{'='*50}\n{msg['content']}"
                for msg in st.session_state.phi_chat_history
            ])
            
            st.download_button(
                label="📥 Télécharger l'historique",
                data=history_text,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                key="download_chat_history"
            )