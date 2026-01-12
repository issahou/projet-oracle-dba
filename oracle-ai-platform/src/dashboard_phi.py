# src/dashboard_phi.py 
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import json


try:
    # Essayer d'importer depuis le bon chemin
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from src.rag_engine import OracleRAGEngine
    print("✅ RAG Engine importé avec succès")
    
    # Créer une classe RAGIntegration fonctionnelle
    class RAGIntegration:
        def __init__(self, llm_engine=None):
            print("🔧 Initialisation RAG Integration...")
            try:
                # Utiliser un fallback si OracleRAGEngine échoue
                try:
                    self.rag_engine = OracleRAGEngine(persist_directory="./data/chroma_db")
                    print("✅ RAG Engine initialisé avec succès")
                except Exception as e:
                    print(f"⚠️ RAG Engine erreur, utilisant fallback: {e}")
                    # Créer un moteur RAG minimal
                    self.rag_engine = self._create_fallback_rag_engine()
                
                self.llm_engine = llm_engine
                print("✅ RAG Integration prête")
            except Exception as e:
                print(f"❌ Erreur initialisation RAG: {e}")
                self.rag_engine = None
                self.llm_engine = None
        
        def _create_fallback_rag_engine(self):
            """Crée un moteur RAG fallback sans dépendances complexes"""
            class FallbackRAGEngine:
                def __init__(self):
                    self.collection = None
                    self.documents = []
                    self.metadatas = []
                    
                    # Charger les 15 documents Oracle de base
                    self._load_documents()
                
                def _load_documents(self):
                    """Charge les 15 documents Oracle de base"""
                    # Les 15 documents complets
                    self.documents = [
                        # SÉCURITÉ (3 docs)
                        """ORACLE BEST PRACTICE: Password Policy Configuration

Une politique de mots de passe forte est essentielle pour la sécurité Oracle.

Configuration recommandée (CREATE PROFILE):
- PASSWORD_LIFE_TIME: 90 jours
- PASSWORD_REUSE_TIME: 365 jours
- PASSWORD_REUSE_MAX: 10
- FAILED_LOGIN_ATTEMPTS: 5
- PASSWORD_LOCK_TIME: 1 jour
- PASSWORD_GRACE_TIME: 7 jours

Exemple:
CREATE PROFILE secure_profile LIMIT
  PASSWORD_LIFE_TIME 90
  PASSWORD_REUSE_TIME 365
  PASSWORD_REUSE_MAX 10
  FAILED_LOGIN_ATTEMPTS 5
  PASSWORD_LOCK_TIME 1
  PASSWORD_GRACE_TIME 7;

ALTER USER production_app PROFILE secure_profile;

Références: Oracle Database Security Guide 19c, Section 5.3""",
                        """ORACLE BEST PRACTICE: Principe du Moindre Privilège

Règles d'or:
1. Éviter GRANT DBA sauf pour admins
2. Éviter SELECT/INSERT/UPDATE/DELETE ANY TABLE
3. Créer des rôles métier spécifiques
4. Utiliser vues pour restreindre accès
5. Révoquer PUBLIC de privilèges non essentiels

Anti-patterns:
- GRANT DBA TO app_user; (CRITIQUE)
- GRANT SELECT ANY TABLE TO PUBLIC; (CRITIQUE)

Bonne pratique:
CREATE ROLE hr_reader;
GRANT SELECT ON employees TO hr_reader;
GRANT hr_reader TO hr_analyst;

Références: Oracle Database Security Guide, Chapitres 4-6""",
                        """ORACLE BEST PRACTICE: Configuration de l'Audit

Configuration minimale:
1. Activer: ALTER SYSTEM SET AUDIT_TRAIL=DB,EXTENDED SCOPE=SPFILE;
2. Échecs connexion: AUDIT CREATE SESSION WHENEVER NOT SUCCESSFUL;
3. Privilèges sensibles: AUDIT SELECT ANY TABLE, DROP ANY TABLE BY ACCESS;
4. Objets critiques: AUDIT ALL ON hr.salaries BY ACCESS;

Types d'audit:
- Standard (AUD$)
- Fine-Grained (FGA)
- Unified (12c+)

Exemple FGA:
BEGIN
  DBMS_FGA.ADD_POLICY(
    object_schema => 'HR',
    object_name => 'EMPLOYEES',
    policy_name => 'salary_audit',
    audit_column => 'SALARY',
    enable => TRUE
  );
END;

Références: Oracle Security Guide, Chapter 27""",
                        
                        # PERFORMANCE (4 docs)
                        """ORACLE BEST PRACTICE: Stratégie d'Indexation

Types d'index:
1. B-Tree (défaut) - haute cardinalité
2. Bitmap - faible cardinalité
3. Function-Based - recherches sur fonctions
4. Composite - requêtes multi-colonnes

Règles:
- Indexer colonnes de jointure (FK)
- Indexer WHERE fréquents
- Indexer ORDER BY
- Éviter colonnes modifiées souvent
- Surveiller V$OBJECT_USAGE

Exemple composite:
CREATE INDEX idx_orders_cust_date ON orders(customer_id, order_date)
  TABLESPACE indx_ts
  PCTFREE 10
  COMPUTE STATISTICS;

Monitoring:
ALTER INDEX idx_name MONITORING USAGE;
SELECT * FROM V$OBJECT_USAGE WHERE USED = 'NO';

Références: Performance Tuning Guide, Chapter 5""",
                        """ORACLE BEST PRACTICE: Hints SQL

Hints essentiels:
1. /*+ INDEX(table index_name) */ - forcer index
2. /*+ FULL(table) */ - full scan
3. /*+ PARALLEL(table, degree) */ - parallélisme
4. /*+ USE_NL(table) */ - nested loop
5. /*+ USE_HASH(table) */ - hash join
6. /*+ LEADING(table) */ - ordre jointures

Exemple:
SELECT /*+ LEADING(d) USE_NL(e) INDEX(e emp_dept_idx) */
       e.*, d.department_name
FROM employees e, departments d
WHERE e.department_id = d.department_id;

Vérification:
EXPLAIN PLAN FOR <requête>;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

Références: SQL Tuning Guide, Chapter 19""",
                        """ORACLE BEST PRACTICE: Réécriture Requêtes

Techniques:
1. ÉVITER SELECT *
2. EXISTS vs IN pour sous-requêtes
3. ÉVITER fonctions dans WHERE
4. BIND VARIABLES
5. ANALYTICAL FUNCTIONS vs GROUP BY

Exemples:
Mauvais: SELECT * FROM employees WHERE UPPER(name) = 'JOHN';
Bon: CREATE INDEX idx_name_upper ON employees(UPPER(name));

Mauvais: WHERE dept_id IN (SELECT id FROM depts WHERE loc = 'NY');
Bon: WHERE EXISTS (SELECT 1 FROM depts d WHERE d.id = e.dept_id AND d.loc = 'NY');

Références: SQL Tuning Guide, Chapter 13""",
                        """ORACLE BEST PRACTICE: Gestion Statistiques

Commandes:
EXEC DBMS_STATS.GATHER_TABLE_STATS(
  ownname => 'HR',
  tabname => 'EMPLOYEES',
  estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE,
  method_opt => 'FOR ALL COLUMNS SIZE AUTO',
  cascade => TRUE
);

Vérifier fraîcheur:
SELECT table_name, last_analyzed, stale_stats
FROM dba_tab_statistics
WHERE owner = 'HR'
ORDER BY last_analyzed NULLS FIRST;

Planification:
- Tables volumineuses: quotidien
- Tables moyennes: hebdomadaire
- Tables référence: mensuel

Stats obsolètes = performances dégradées!

Références: Performance Tuning Guide, Chapter 13""",
                        
                        # BACKUP (2 docs)
                        """ORACLE BEST PRACTICE: Stratégie RMAN

Selon RPO/RTO:
1. RPO < 1h: Incrémental horaire
RUN {
  BACKUP INCREMENTAL LEVEL 1 DATABASE PLUS ARCHIVELOG DELETE INPUT;
}

2. RPO < 24h: Quotidien
RUN {
  BACKUP AS COMPRESSED BACKUPSET DATABASE PLUS ARCHIVELOG;
  BACKUP CURRENT CONTROLFILE;
}

Configuration:
CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF 7 DAYS;
CONFIGURE CONTROLFILE AUTOBACKUP ON;
CONFIGURE DEVICE TYPE DISK PARALLELISM 4;

Vérification:
BACKUP VALIDATE DATABASE;
LIST BACKUP SUMMARY;
REPORT OBSOLETE;

Sauvegarde non testée = pas de sauvegarde!

Références: Backup and Recovery User's Guide""",
                        """ORACLE BEST PRACTICE: Archive Logs

Activer ARCHIVELOG:
SHUTDOWN IMMEDIATE;
STARTUP MOUNT;
ALTER DATABASE ARCHIVELOG;
ALTER DATABASE OPEN;

Configuration:
ALTER SYSTEM SET LOG_ARCHIVE_DEST_1='LOCATION=/u01/archive';
ALTER SYSTEM SET LOG_ARCHIVE_FORMAT='arch_%t_%s_%r.arc';

Surveillance:
SELECT * FROM V$RECOVERY_FILE_DEST;
SELECT space_limit/1024/1024 as limit_mb, 
       space_used/1024/1024 as used_mb
FROM V$RECOVERY_FILE_DEST;

Nettoyage RMAN:
DELETE ARCHIVELOG ALL COMPLETED BEFORE 'SYSDATE-7';

Espace insuffisant = arrêt base!

Références: Administrator's Guide, Chapter 11""",
                        
                        # ANOMALIES (3 docs)
                        """ORACLE ANOMALY: Scans Tables Système

Indicateurs:
1. SELECT sur SYS.USER$
2. SELECT DBA_USERS suspect
3. Accès SYS.LINK$
4. Énumération DBA_TAB_PRIVS
5. V$SESSION depuis non-admin

Exemples suspects:
SELECT username, password FROM sys.user$ WHERE type# = 0;
SELECT * FROM dba_sys_privs WHERE privilege LIKE '%ANY%';

Détection:
SELECT userid, obj$name, returncode
FROM sys.aud$
WHERE obj$creator = 'SYS'
AND obj$name IN ('USER$', 'LINK$')
AND userid NOT IN ('SYS', 'SYSTEM');

Actions:
ALTER USER suspect ACCOUNT LOCK;
REVOKE SELECT ANY DICTIONARY FROM suspect;

CRITIQUE: Tentative reconnaissance pour attaque

Références: Security Guide, Chapter 18""",
                        """ORACLE ANOMALY: Escalade Privilèges

Patterns:
1. GRANT DBA à non-admin
2. GRANT SYSDBA hors heures
3. Nouveaux users avec DBA
4. Modification profils
5. Ajout privilèges ANY

Exemples:
GRANT DBA TO app_user;
CREATE ROLE elevated_role;
GRANT SELECT ANY TABLE TO elevated_role;

Détection:
SELECT grantee, privilege, timestamp
FROM dba_sys_privs_audit
WHERE privilege IN ('DBA', 'SYSDBA')
OR privilege LIKE '%ANY%';

Actions:
REVOKE DBA FROM suspicious_user;
ALTER USER suspicious_user ACCOUNT LOCK;
ALTER SYSTEM KILL SESSION 'sid,serial#';

ALERTE: Escalade = compromission potentielle

Références: Security Guide, Chapters 3-4""",
                        """ORACLE ANOMALY: DDL Suspects

Opérations à surveiller:
1. DROP TABLE/INDEX/USER en prod
2. ALTER TABLE hors maintenance
3. TRUNCATE tables critiques
4. CREATE USER par non-admin
5. ALTER SYSTEM SET

Exemples:
DROP TABLE financial_transactions PURGE;
ALTER TABLE employees DROP COLUMN salary;

Détection:
SELECT username, action_name, obj_name
FROM dba_audit_trail
WHERE action_name IN ('DROP TABLE', 'TRUNCATE TABLE')
AND username NOT IN ('ADMIN');

Prévention trigger:
CREATE TRIGGER ddl_prevention
BEFORE DDL ON SCHEMA
BEGIN
  IF SESSION_USER NOT IN ('DBA') THEN
    RAISE_APPLICATION_ERROR(-20001, 'DDL interdit');
  END IF;
END;

DDL non planifié = risque perte données

Références: Administrator's Guide, Chapter 23""",
                        
                        # MONITORING (2 docs)
                        """ORACLE BEST PRACTICE: Vues Performance

Vues essentielles:
1. V$SESSION - sessions actives
2. V$SQL - requêtes en cache
3. V$SYSTEM_EVENT - attentes
4. V$SQLSTAT - stats SQL
5. V$LOCK - verrous

Exemples:
SELECT sid, username, sql_id, blocking_session
FROM v$session
WHERE username IS NOT NULL;

SELECT sql_id, elapsed_time, executions
FROM v$sql
WHERE elapsed_time > 1000000
ORDER BY elapsed_time DESC;

Scripts monitoring:
- Top 10 requêtes lentes
- Sessions bloquantes
- Objets invalides
- Espace tablespace

Références: Database Reference Guide""",
                        """ORACLE BEST PRACTICE: AWR

Configuration:
EXEC DBMS_WORKLOAD_REPOSITORY.MODIFY_SNAPSHOT_SETTINGS(
  interval => 30,
  retention => 14*24*60
);

Générer rapport:
@$ORACLE_HOME/rdbms/admin/awrrpt.sql

Sections clés:
- SQL Statistics: requêtes coûteuses
- Wait Events: attentes principales
- Instance Efficiency: hit ratios
- Load Profile: transactions/sec
- Time Model: DB Time, CPU

Interprétation:
- DB Time > DB CPU = attentes I/O
- Buffer Hit < 90% = manque SGA
- Top SQL = cibles optimisation

AWR = source #1 diagnostic perf

Références: Performance Tuning Guide, Chapter 8""",
                        
                        # TROUBLESHOOTING (1 doc)
                        """ORACLE TROUBLESHOOTING: Sessions Bloquantes

Identifier:
SELECT s1.sid as blocked_sid,
       s2.sid as blocking_sid,
       s1.sql_id,
       s1.seconds_in_wait
FROM v$session s1, v$session s2
WHERE s1.blocking_session = s2.sid
ORDER BY s1.seconds_in_wait DESC;

Voir SQL:
SELECT sql_text FROM v$sql WHERE sql_id = '<id>';

Détails verrou:
SELECT object_name, locked_mode
FROM v$locked_object lo, dba_objects do
WHERE lo.object_id = do.object_id
AND lo.session_id = <sid>;

Solutions:
a) Attendre si légitime
b) Demander commit/rollback
c) Kill: ALTER SYSTEM KILL SESSION 'sid,serial#';

Prévention:
- Commits réguliers
- SELECT FOR UPDATE NOWAIT
- Index optimaux

Références: Administrator's Guide, Chapter 16"""
                    ]
                    
                    # Métadonnées correspondantes aux 15 documents
                    self.metadatas = [
                        # SÉCURITÉ (3 docs)
                        {'category': 'security', 'topic': 'password_policy', 'severity': 'CRITICAL', 'source': 'oracle_internal'},
                        {'category': 'security', 'topic': 'least_privilege', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        {'category': 'security', 'topic': 'audit_configuration', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        
                        # PERFORMANCE (4 docs)
                        {'category': 'performance', 'topic': 'index_strategy', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        {'category': 'performance', 'topic': 'sql_hints', 'severity': 'MEDIUM', 'source': 'oracle_internal'},
                        {'category': 'performance', 'topic': 'query_rewrite', 'severity': 'MEDIUM', 'source': 'oracle_internal'},
                        {'category': 'performance', 'topic': 'statistics_management', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        
                        # BACKUP (2 docs)
                        {'category': 'backup', 'topic': 'rman_strategy', 'severity': 'CRITICAL', 'source': 'oracle_internal'},
                        {'category': 'backup', 'topic': 'archivelog_management', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        
                        # ANOMALIES (3 docs)
                        {'category': 'anomaly', 'topic': 'suspicious_scans', 'severity': 'CRITICAL', 'source': 'oracle_internal'},
                        {'category': 'anomaly', 'topic': 'privilege_escalation', 'severity': 'CRITICAL', 'source': 'oracle_internal'},
                        {'category': 'anomaly', 'topic': 'ddl_operations', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        
                        # MONITORING (2 docs)
                        {'category': 'monitoring', 'topic': 'performance_views', 'severity': 'MEDIUM', 'source': 'oracle_internal'},
                        {'category': 'monitoring', 'topic': 'awr_reports', 'severity': 'HIGH', 'source': 'oracle_internal'},
                        
                        # TROUBLESHOOTING (1 doc)
                        {'category': 'troubleshooting', 'topic': 'blocking_sessions', 'severity': 'HIGH', 'source': 'oracle_internal'}
                    ]
                
                def count(self):
                    return len(self.documents)
                
                def query(self, question, n_results=5):
                    """Recherche simple basée sur mots-clés"""
                    results = []
                    for i, (doc, meta) in enumerate(zip(self.documents, self.metadatas)):
                        score = self._calculate_similarity(question, doc)
                        if score > 0.1:  # Seuil bas pour simplicité
                            results.append({
                                'document': doc,
                                'metadata': meta,
                                'similarity_score': score
                            })
                    
                    # Trier par score et retourner les meilleurs
                    results.sort(key=lambda x: x['similarity_score'], reverse=True)
                    return results[:n_results]
                
                def _calculate_similarity(self, query, document):
                    """Calcul de similarité simple basé sur mots communs"""
                    query_words = set(query.lower().split())
                    doc_words = set(document.lower().split())
                    common = len(query_words.intersection(doc_words))
                    total = len(query_words.union(doc_words))
                    return common / total if total > 0 else 0
                
                def get_collection_stats(self):
                    categories = {}
                    topics = {}
                    
                    for meta in self.metadatas:
                        cat = meta.get('category', 'unknown')
                        topic = meta.get('topic', 'unknown')
                        categories[cat] = categories.get(cat, 0) + 1
                        topics[topic] = topics.get(topic, 0) + 1
                    
                    return {
                        'total_documents': len(self.documents),
                        'categories': categories,
                        'topics': topics,
                        'categories_distribution': categories
                    }
            
            return FallbackRAGEngine()
        
        def get_collection_stats(self):
            if not self.rag_engine:
                return {'total_documents': 0, 'categories': {}, 'topics': {}, 'categories_distribution': {}}
            
            try:
                stats = self.rag_engine.get_collection_stats()
                print(f"📊 Stats RAG: {stats['total_documents']} documents")
                return stats
            except Exception as e:
                print(f"❌ Erreur stats RAG: {e}")
                return {'total_documents': 0, 'categories': {}, 'topics': {}, 'categories_distribution': {}}
        
        def retrieve_context(self, query, n_results=5):
            if not self.rag_engine:
                return []
            
            try:
                results = self.rag_engine.query(query, n_results)
                
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'content': result['document'][:500],
                        'metadata': result['metadata'],
                        'distance': 1 - result['similarity_score'] if 'similarity_score' in result else 0.5
                    })
                
                print(f"📚 {len(formatted_results)} documents récupérés pour: '{query[:30]}...'")
                return formatted_results
            except Exception as e:
                print(f"❌ Erreur retrieve_context: {e}")
                return []
        
        def search_by_category(self, category, query, n_results=5):
            return self.retrieve_context(f"{query} {category}", n_results)
        
        def add_custom_document(self, content, category, topic, metadata):
            if not self.rag_engine:
                return False
            
            try:
                metadata.update({
                    'category': category,
                    'topic': topic,
                    'source': 'custom',
                    'added_date': datetime.now().strftime('%Y-%m-%d')
                })
                
                # Vérifier si le moteur a la méthode add_document
                if hasattr(self.rag_engine, 'add_document'):
                    success = self.rag_engine.add_document(content, metadata)
                    return success
                else:
                    # Fallback pour les moteurs sans add_document
                    if hasattr(self.rag_engine, 'documents'):
                        self.rag_engine.documents.append(content)
                        self.rag_engine.metadatas.append(metadata)
                        return True
                    return False
            except Exception as e:
                print(f"❌ Erreur add_document: {e}")
                return False
        
        def test_retrieval(self):
            test_queries = [
                "index lent performance",
                "sécurité mot de passe Oracle",
                "backup RMAN stratégie",
                "requête SELECT performance",
                "audit Oracle configuration"
            ]
            
            results = {}
            for query in test_queries:
                docs = self.retrieve_context(query, 3)
                results[query] = {
                    'found': len(docs),
                    'top_topics': [doc['metadata'].get('topic', 'N/A') for doc in docs[:2]] if docs else [],
                    'relevance': [1 - doc.get('distance', 0.5) for doc in docs[:2]] if docs else []
                }
                print(f"📚 {len(docs)} documents récupérés pour: '{query}'")
            
            return results
        
        def enhanced_llm_query(self, prompt):
            """Utilise LLM avec contexte RAG"""
            if not self.llm_engine:
                return "LLM non disponible. Veuillez lancer Ollama avec 'ollama serve'"
            
            try:
                # Récupérer contexte RAG
                context_docs = self.retrieve_context(prompt, 3)
                
                if context_docs:
                    # Construire le contexte
                    context_text = "\n\nCONTEXTE RAG:\n"
                    for i, doc in enumerate(context_docs, 1):
                        context_text += f"\n--- Document {i} ---\n"
                        context_text += f"Catégorie: {doc['metadata'].get('category', 'N/A')}\n"
                        context_text += f"Topic: {doc['metadata'].get('topic', 'N/A')}\n"
                        context_text += f"Contenu: {doc['content'][:300]}...\n"
                    
                    prompt_with_context = f"{context_text}\n\nQUESTION: {prompt}\n\nRÉPONSE:"
                    
                    # Appeler le LLM
                    if hasattr(self.llm_engine, 'generate'):
                        response = self.llm_engine.generate(
                            "chatbot_general",
                            variables={"query": prompt_with_context, "history": ""},
                            max_tokens=500
                        )
                    elif hasattr(self.llm_engine, 'chat_response'):
                        response = self.llm_engine.chat_response(prompt_with_context, "")
                    else:
                        response = "Format de réponse LLM non supporté"
                    
                    return response
                else:
                    # Fallback sans RAG
                    if hasattr(self.llm_engine, 'chat_response'):
                        return self.llm_engine.chat_response(prompt, "")
                    else:
                        return f"Question: {prompt}\n\nRéponse: Je suis votre assistant Oracle AI. Je traite actuellement votre question. RAG context disponible: Non"
                        
            except Exception as e:
                return f"Erreur lors du traitement: {str(e)}"

    # Fonction d'initialisation
    def initialize_rag_for_dashboard(llm_engine):
        return RAGIntegration(llm_engine=llm_engine)

except ImportError as e:
    print(f"⚠️ RAG import error: {e}")
    # Définir des classes mock pour éviter les erreurs
    class MockRAGIntegration:
        def __init__(self):
            print("⚠️ RAG en mode mock")
            pass
        def get_collection_stats(self):
            return {'total_documents': 15, 'categories': {'security': 3, 'performance': 4, 'backup': 2, 'anomaly': 3, 'monitoring': 2, 'troubleshooting': 1}, 'topics': {}, 'categories_distribution': {}}
        def retrieve_context(self, query, n_results=5):
            return []
        def search_by_category(self, category, query, n_results=5):
            return []
        def add_custom_document(self, content, category, topic, metadata):
            return True
        def test_retrieval(self):
            return {}
        def enhanced_llm_query(self, prompt):
            return "RAG non disponible - réponse générique"

    def initialize_rag_for_dashboard(llm_engine):
        return MockRAGIntegration()

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Configuration du thème professionnel
COLORS = {
    'primary': '#1e3a8a',      # Bleu foncé
    'secondary': '#3b82f6',    # Bleu moderne
    'success': '#10b981',      # Vert
    'warning': '#f59e0b',      # Orange
    'danger': '#ef4444',       # Rouge
    'neutral': '#6b7280',      # Gris
    'bg_light': '#f8fafc',     # Fond clair
    'text_dark': '#1e293b'     # Texte foncé
}

class OracleAIDashboardPhi:
    def __init__(self):
        st.set_page_config(
            page_title="Oracle AI Platform ",
            page_icon="⚡",
            layout="wide"
        )
        
        # Appliquer le CSS professionnel
        self._apply_professional_css()
        
        # Initialisation
        self.llm_engine = None
        self.auditor = None
        self.mock_data = None
        self.model_name = "simulate"
        self.rag_integration = None  
        
        # Démarrer l'initialisation
        self._init_components()
    
    def _apply_professional_css(self):
        """Applique un style CSS professionnel et épuré"""
        st.markdown(f"""
        <style>
        /* Theme général professionnel */
        .stApp {{
            background-color: #ffffff;
        }}
        
        /* En-têtes professionnels */
        h1 {{
            color: {COLORS['primary']};
            font-weight: 600;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            border-bottom: 3px solid {COLORS['secondary']};
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        
        h2, h3 {{
            color: {COLORS['text_dark']};
            font-weight: 500;
            margin-top: 1.5rem;
        }}
        
        /* Sidebar professionnel */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['bg_light']};
            border-right: 1px solid #e2e8f0;
        }}
        
        [data-testid="stSidebar"] h1 {{
            color: {COLORS['primary']};
            font-size: 1.5rem;
            font-weight: 700;
            border-bottom: 2px solid {COLORS['secondary']};
            padding-bottom: 0.75rem;
        }}
        
        /* Boutons élégants */
        .stButton > button {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .stButton > button:hover {{
            background-color: {COLORS['secondary']};
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }}
        
        /* Métriques professionnelles */
        [data-testid="stMetricValue"] {{
            color: {COLORS['primary']};
            font-size: 2rem;
            font-weight: 600;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {COLORS['neutral']};
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Cards avec ombres subtiles */
        .element-container {{
            background-color: white;
        }}
        
        div[data-testid="stExpander"] {{
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        /* Messages professionnels */
        .stSuccess {{
            background-color: #ecfdf5;
            border-left: 4px solid {COLORS['success']};
            padding: 1rem;
            border-radius: 4px;
        }}
        
        .stWarning {{
            background-color: #fffbeb;
            border-left: 4px solid {COLORS['warning']};
            padding: 1rem;
            border-radius: 4px;
        }}
        
        .stError {{
            background-color: #fef2f2;
            border-left: 4px solid {COLORS['danger']};
            padding: 1rem;
            border-radius: 4px;
        }}
        
        .stInfo {{
            background-color: #eff6ff;
            border-left: 4px solid {COLORS['secondary']};
            padding: 1rem;
            border-radius: 4px;
        }}
        
        /* Tables élégantes */
        .dataframe {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .dataframe thead tr {{
            background-color: {COLORS['bg_light']};
            color: {COLORS['text_dark']};
            font-weight: 600;
        }}
        
        /* Code blocks professionnels */
        .stCodeBlock {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-family: 'Monaco', 'Courier New', monospace;
        }}
        
        /* Dividers subtils */
        hr {{
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 1.5rem 0;
        }}
        
        /* Chat messages */
        .stChatMessage {{
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        
        /* Radio buttons professionnels */
        .stRadio > div {{
            gap: 0.5rem;
        }}
        
        .stRadio label {{
            background-color: white;
            padding: 0.75rem 1rem;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .stRadio label:hover {{
            border-color: {COLORS['secondary']};
            background-color: {COLORS['bg_light']};
        }}
        
        /* Selectbox élégant */
        .stSelectbox {{
            border-radius: 6px;
        }}
        
        /* Spinner professionnel */
        .stSpinner > div {{
            border-top-color: {COLORS['secondary']} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def _init_components(self):
        """Initialise les composants pour Phi + RAG"""
        if 'phi_initialized' not in st.session_state:
            print("🚀 Initialisation pour Phi + RAG...")
            
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
                    self.llm_engine = None
                    
            except Exception as e:
                print(f"❌ Erreur Phi: {e}")
                self.model_name = "simulate"
                self.llm_engine = None
            
            # 2. Initialiser RAG 
            try:
                print("📚 Initialisation RAG ChromaDB...")
                self.rag_integration = initialize_rag_for_dashboard(self.llm_engine)
                
                # Stocker dans session
                st.session_state.rag_integration = self.rag_integration
                
                # Obtenir stats RAG
                if self.rag_integration:
                    rag_stats = self.rag_integration.get_collection_stats()
                    st.session_state.rag_stats = rag_stats
                    print(f"✅ RAG initialisé: {rag_stats.get('total_documents', 0)} documents")
                else:
                    st.session_state.rag_stats = {'total_documents': 0, 'categories': {}}
                    print("❌ RAG non initialisé")
                
            except Exception as e:
                print(f"⚠️ RAG en mode dégradé: {e}")
                self.rag_integration = None
                st.session_state.rag_integration = None
                st.session_state.rag_stats = {'total_documents': 0, 'categories': {}}
            
            # 3. Initialiser l'auditeur avec le bon engine
            try:
                from src.security_audit import SecurityAuditor
                self.auditor = SecurityAuditor(llm_engine=self.llm_engine)
                print("✅ Security Auditor initialisé")
            except Exception as e:
                print(f"⚠️ Audit simulation: {e}")
                self.auditor = None
            
            # 4. Créer des données mock
            self.mock_data = self._create_phi_mock_data()
            
            # 5. Stocker dans session
            st.session_state.llm_engine = self.llm_engine
            st.session_state.auditor = self.auditor
            st.session_state.mock_data = self.mock_data
            st.session_state.model_name = self.model_name
            st.session_state.phi_initialized = True
            
            print("🎉 Initialisation Phi + RAG terminée")
        else:
            # Récupérer depuis session
            self.llm_engine = st.session_state.get('llm_engine')
            self.auditor = st.session_state.get('auditor')
            self.mock_data = st.session_state.get('mock_data')
            self.model_name = st.session_state.get('model_name', 'simulate')
            self.rag_integration = st.session_state.get('rag_integration')
    
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
        """Barre latérale optimisée avec RAG"""
        with st.sidebar:
            # En-tête élégant
            st.markdown(f"""
            <div style='text-align: center; padding: 1rem 0;'>
                <h1 style='color: {COLORS["primary"]}; margin: 0;'>
                    ⚡ Oracle AI
                </h1>
                <p style='color: {COLORS["neutral"]}; font-size: 0.9rem; margin-top: 0.5rem;'>
                    Intelligence Platform
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Menu de navigation
            menu = st.radio(
                "Navigation",
                ["🏠 Dashboard", "🔒 Sécurité", "⚡ Performance", "💾 Sauvegarde", "🤖 Chat", "📚 Base Connaissances"],
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Statut système
            st.markdown("### 📊 Statut Système")
            
            # Badge de statut IA
            ai_status = "🟢 Actif" if self.model_name == "phi:latest" else "🟡 Simulation"
            ai_color = COLORS['success'] if self.model_name == "phi:latest" else COLORS['warning']
            
            st.markdown(f"""
            <div style='background-color: {COLORS["bg_light"]}; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 500; color: {COLORS["neutral"]}'>Modèle IA</span>
                    <span style='color: {ai_color}; font-weight: 600;'>{ai_status}</span>
                </div>
                <div style='font-size: 0.85rem; color: {COLORS["neutral"]}; margin-top: 0.5rem;'>
                    {self.model_name}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Stats RAG
            rag_stats = st.session_state.get('rag_stats', {})
            rag_docs = rag_stats.get('total_documents', 0)
            
            st.markdown(f"""
            <div style='background-color: {COLORS["bg_light"]}; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 500; color: {COLORS["neutral"]}'>Base Connaissances</span>
                    <span style='color: {COLORS["primary"]}; font-weight: 600;'>{rag_docs} docs</span>
                </div>
                <div style='font-size: 0.85rem; color: {COLORS["neutral"]}; margin-top: 0.5rem;'>
                    Documents Oracle techniques
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Connexion
            if self.llm_engine and hasattr(self.llm_engine, 'test_connection'):
                success, msg = self.llm_engine.test_connection()
                conn_status = "✅ Connecté" if success else "❌ Déconnecté"
                conn_color = COLORS['success'] if success else COLORS['danger']
                
                st.markdown(f"""
                <div style='background-color: {COLORS["bg_light"]}; padding: 1rem; border-radius: 8px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-weight: 500; color: {COLORS["neutral"]}'>Connexion IA</span>
                        <span style='color: {conn_color}; font-weight: 600;'>{conn_status}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Actions
            st.markdown("### ⚙️ Actions")
            
            if st.button("🔄 Actualiser IA", use_container_width=True):
                # Nettoyer la session pour réinitialiser
                keys_to_delete = ['phi_initialized', 'rag_integration', 'rag_stats']
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            if st.button("🧪 Tester RAG", use_container_width=True):
                st.session_state.test_rag = True
            
            if st.button("📊 Debug", use_container_width=True):
                st.session_state.show_debug = True
            
            st.markdown("---")
            
            # Footer
            st.markdown(f"""
            <div style='text-align: center; padding: 1rem 0; color: {COLORS["neutral"]}; font-size: 0.8rem;'>
                <p>Oracle AI Platform v2.0</p>
                <p style='margin-top: 0.5rem;'>Powered by Phi AI + RAG</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Convertir le menu
        menu_map = {
            "🏠 Dashboard": "home",
            "🔒 Sécurité": "security", 
            "⚡ Performance": "performance",
            "💾 Sauvegarde": "backup",
            "🤖 Chat": "chat",
            "📚 Base Connaissances": "knowledge_base"
        }
        return menu_map.get(menu, "home")
    
    def home_page(self):
        """Page d'accueil professionnelle"""
        # En-tête avec design professionnel
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 2rem; color: white;'>
            <h1 style='color: white; border: none; margin: 0; padding: 0;'>Oracle AI Platform</h1>
            <p style='font-size: 1.1rem; margin-top: 0.5rem; opacity: 0.9;'>
                Plateforme d'intelligence artificielle pour Oracle Database avec RAG
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "ACTIF" if self.model_name == "phi:latest" else "SIMULATION"
            st.metric("🤖 Statut IA", status)
        
        with col2:
            st.metric("📊 Requêtes", "12", "+2")
        
        with col3:
            rag_stats = st.session_state.get('rag_stats', {})
            rag_docs = rag_stats.get('total_documents', 0)
            st.metric("📚 Docs RAG", rag_docs)
        
        with col4:
            st.metric("⚡ Temps Réponse", "< 2s")
        
        st.markdown("---")
        
        # Capacités
        st.markdown("### 🎯 Capacités de la Plateforme")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style='background-color: white; padding: 1.5rem; border-radius: 8px; 
                        border: 1px solid #e2e8f0; height: 100%;'>
                <h4 style='color: {COLORS["primary"]}; margin-top: 0;'>🔍 Audit & Sécurité</h4>
                <p style='color: {COLORS["neutral"]}; line-height: 1.6;'>
                    Analyse complète des configurations de sécurité Oracle avec identification 
                    automatique des vulnérabilités et recommandations détaillées.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background-color: white; padding: 1.5rem; border-radius: 8px; 
                        border: 1px solid #e2e8f0; height: 100%;'>
                <h4 style='color: {COLORS["primary"]}; margin-top: 0;'>💾 Stratégie Backup</h4>
                <p style='color: {COLORS["neutral"]}; line-height: 1.6;'>
                    Plans de sauvegarde RMAN personnalisés avec scripts exécutables 
                    adaptés à vos objectifs RPO et RTO.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color: white; padding: 1.5rem; border-radius: 8px; 
                        border: 1px solid #e2e8f0; height: 100%;'>
                <h4 style='color: {COLORS["primary"]}; margin-top: 0;'>⚡ Optimisation SQL</h4>
                <p style='color: {COLORS["neutral"]}; line-height: 1.6;'>
                    Diagnostic approfondi des requêtes lentes avec analyse des plans d'exécution 
                    et suggestions d'indexation optimale enrichies par RAG.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background-color: white; padding: 1.5rem; border-radius: 8px; 
                        border: 1px solid #e2e8f0; height: 100%;'>
                <h4 style='color: {COLORS["primary"]}; margin-top: 0;'>📚 Base Connaissances</h4>
                <p style='color: {COLORS["neutral"]}; line-height: 1.6;'>
                    Base documentaire Oracle enrichie (RAG) avec 15 documents techniques 
                    sur sécurité, performance, backup et dépannage.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Test RAG détaillé
        if st.session_state.get('test_rag'):
            st.markdown("---")
            self._test_rag_integration()
            st.session_state.test_rag = False
        
        # Test Phi détaillé
        if st.session_state.get('test_phi_detailed'):
            st.markdown("---")
            self._test_phi_detailed()
            st.session_state.test_phi_detailed = False
        
        # Debug info
        if st.session_state.get('show_debug'):
            with st.expander("🔧 Debug Information"):
                st.write(f"**Modèle:** {self.model_name}")
                st.write(f"**Engine type:** {type(self.llm_engine).__name__ if self.llm_engine else 'None'}")
                
                rag = st.session_state.get('rag_integration')
                st.write(f"**RAG disponible:** {'Oui' if rag else 'Non'}")
                
                if rag:
                    try:
                        stats = rag.get_collection_stats()
                        st.write(f"**Documents RAG:** {stats.get('total_documents', 0)}")
                        st.write(f"**Categories RAG:** {list(stats.get('categories', {}).keys())}")
                    except Exception as e:
                        st.write(f"**Erreur stats RAG:** {e}")
                
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
        
    def _test_rag_integration(self):
        """Test l'intégration RAG"""
        st.subheader("🧪 Test RAG Integration")
        
        rag = st.session_state.get('rag_integration')
        
        if not rag:
            st.error("❌ RAG non initialisé")
            return
        
        with st.spinner("Tests en cours..."):
            # Stats
            stats = rag.get_collection_stats()
            st.write(f"**Documents:** {stats.get('total_documents', 0)}")
            
            categories = stats.get('categories', {})
            if categories:
                st.write(f"**Catégories:** {list(categories.keys())}")
            
            # Test de recherche
            test_query = "index lent performance"
            results = rag.retrieve_context(test_query, 3)
            st.write(f"**Test '{test_query}':** {len(results)} résultats")
            
            for i, doc in enumerate(results, 1):
                with st.expander(f"Résultat {i}"):
                    st.write(f"**Métadonnées:** {doc.get('metadata', {})}")
                    if doc.get('content'):
                        st.write(f"**Contenu:** {doc['content'][:200]}...")
        
        st.success("✅ Tests RAG terminés")
    
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
                    
                    # Améliorer le rapport avec RAG si disponible
                    if self.rag_integration:
                        report = self._enhance_security_report_with_rag(report, security_data)
                    
                    st.session_state.detailed_audit_report = report
                    
                    # Afficher les résultats
                    self._display_audit_results(report)
                    
                else:
                    st.error("Auditeur non disponible")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'audit: {str(e)}")
    
    def _enhance_security_report_with_rag(self, report, security_data):
        """Améliore le rapport avec RAG"""
        if not self.rag_integration:
            return report
        
        try:
            # Rechercher des documents pertinents
            query = "sécurité Oracle meilleures pratiques"
            rag_results = self.rag_integration.retrieve_context(query, 3)
            
            if rag_results:
                report['rag_enhanced'] = True
                report['rag_references'] = []
                
                for doc in rag_results:
                    report['rag_references'].append({
                        'source': doc.get('metadata', {}).get('category', 'N/A'),
                        'topic': doc.get('metadata', {}).get('topic', 'N/A'),
                        'content': doc.get('content', '')[:200] + "..."
                    })
        
        except Exception as e:
            print(f"Erreur enhancement RAG: {e}")
        
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
        
        # Afficher les références RAG si disponibles
        if report.get('rag_enhanced') and report.get('rag_references'):
            with st.expander("📚 Références de la Base de Connaissances"):
                for ref in report['rag_references']:
                    st.caption(f"**{ref['source']} - {ref['topic']}**")
                    st.write(ref['content'])
        
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
                if self.rag_integration and self.llm_engine:
                    # Rechercher dans RAG
                    rag_results = self.rag_integration.retrieve_context("optimisation requête SQL", 2)
                    
                    # Afficher les résultats
                    st.success("✅ Analyse complète terminée!")
                    
                    with st.expander("📋 Rapport d'optimisation complet", expanded=True):
                        # Section RAG
                        if rag_results:
                            st.subheader("📚 Connaissances de Référence")
                            for doc in rag_results:
                                with st.expander(f"Source: {doc.get('metadata', {}).get('category', 'N/A')} - {doc.get('metadata', {}).get('topic', 'N/A')}"):
                                    if doc.get('content'):
                                        st.markdown(doc['content'][:500] + "...")
                        
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
    
    def _create_optimization_script(self, query_data):
        """Crée un script SQL complet d'optimisation"""
        return f"""-- Script d'optimisation pour: {query_data['SQL_ID']}
-- Généré par Oracle AI Platform + RAG
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
        st.info("Analyse basique (sans RAG/LLM)")
        st.write(f"**Problème:** {query_data['PROBLEM']}")
        st.write(f"**Temps:** {query_data['ELAPSED_TIME_MS']}ms")
        st.write(f"**CPU:** {query_data['CPU_PERCENT']}%")
    
    def backup_page(self):
        """Page backup améliorée"""
        st.title("💾 Stratégie de Sauvegarde Avancée")
        
        # Configuration interactive
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
        
        # Bouton de génération
        if st.button("🎯 Générer la stratégie optimale", type="primary"):
            self._generate_advanced_backup_strategy(
                rpo, rto, data_size, criticality,
                storage_type,
                compression,
                encryption
            )
        
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
                
                if self.rag_integration:
                    # Utiliser RAG pour enrichir
                    rag_results = self.rag_integration.retrieve_context("sauvegarde RMAN stratégie", 2)
                    st.session_state.last_backup_strategy = {
                        'requirements': requirements,
                        'rag_references': rag_results,
                        'strategy': self._create_backup_strategy(requirements)
                    }
                else:
                    st.warning("Mode simulation - Stratégie par défaut")
                    self._show_default_backup_strategy(requirements)
                    
            except Exception as e:
                st.error(f"❌ Erreur génération stratégie: {str(e)}")
    
    def _create_backup_strategy(self, requirements):
        """Crée une stratégie de backup basée sur les besoins"""
        return {
            "type": "INCREMENTAL_LEVEL_1",
            "frequency": "HOURLY" if requirements['rpo'] == "15 minutes" else "DAILY",
            "retention_days": 30,
            "storage": requirements['storage'],
            "estimated_cost": 2500,
            "advantages": f"RPO: {requirements['rpo']}, RTO: {requirements['rto']}",
            "limitations": "Nécessite espace disque important"
        }
    
    def _display_backup_results(self, strategy):
        """Affiche les résultats de la stratégie de backup"""
        if not isinstance(strategy, dict):
            st.error("Format de stratégie invalide")
            return
        
        st.success("✅ Stratégie générée avec succès!")
        
        # Afficher les références RAG si disponibles
        if strategy.get('rag_references'):
            with st.expander("📚 Références de la Base de Connaissances"):
                for doc in strategy['rag_references']:
                    st.caption(f"**{doc.get('metadata', {}).get('category', 'N/A')} - {doc.get('metadata', {}).get('topic', 'N/A')}**")
                    if doc.get('content'):
                        st.write(doc['content'][:200] + "...")
        
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
        
        rman_script = self._create_rman_script(strategy.get('requirements', {}))
        if rman_script:
            st.code(rman_script, language="sql")
            
            # Boutons d'action
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
        
        steps = [
            "Étape 1: Vérifier l'espace disque: SELECT * FROM V$ASM_DISKGROUP;",
            "Étape 2: Configurer les paramètres: ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = 500G;",
            "Étape 3: Créer le script de planification: /u01/app/oracle/scripts/rman_backup.sh",
            "Étape 4: Tester la restauration complète sur environnement de test",
            "Étape 5: Configurer les alertes OEM pour les échecs de backup",
            "Étape 6: Documenter la procédure de restauration d'urgence"
        ]
        
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")
    
    def _create_rman_script(self, requirements):
        """Crée un script RMAN basé sur les besoins"""
        return f"""-- Stratégie de sauvegarde Oracle RMAN
-- Configuration pour: RPO={requirements.get('rpo', 'N/A')}, RTO={requirements.get('rto', 'N/A')}
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
}}"""
    
    def _show_default_backup_strategy(self, requirements):
        """Affiche une stratégie de backup par défaut"""
        default_strategy = {
            "requirements": requirements,
            "strategy": {
                "type": "INCREMENTAL_LEVEL_1",
                "frequency": "HOURLY",
                "retention_days": 30,
                "storage": "ASM",
                "estimated_cost": 2500,
                "advantages": "RPO court, Restauration rapide, Impact minimal production",
                "limitations": "Nécessite ASM, Espace disque important"
            }
        }
        
        st.session_state.last_backup_strategy = default_strategy
        self._display_backup_results(default_strategy)
    
    def knowledge_base_page(self):
        """Page de gestion de la base de connaissances RAG"""
        st.title("📚 Base de Connaissances Oracle (RAG)")
        
        # Récupérer RAG depuis session state
        rag = st.session_state.get('rag_integration')
        
        if not rag:
            st.warning("⚠️ RAG non initialisé")
            st.info("Pour activer RAG, assurez-vous que ChromaDB est installé et initialisé")
            
            # Essayer d'initialiser RAG
            if st.button("🔄 Initialiser RAG"):
                try:
                    self.rag_integration = initialize_rag_for_dashboard(self.llm_engine)
                    st.session_state.rag_integration = self.rag_integration
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur initialisation: {e}")
            return
        
        # Onglets
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Statistiques", "🔍 Recherche", "➕ Ajouter", "🧪 Tests"])
        
        with tab1:
            st.subheader("Statistiques de la Collection")
            
            stats = rag.get_collection_stats()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Documents Totaux", stats.get('total_documents', 0))
            with col2:
                st.metric("Catégories", len(stats.get('categories', {})))
            with col3:
                st.metric("Topics", len(stats.get('topics', {})))
            
            # Répartition par catégorie
            st.subheader("Répartition par Catégorie")
            categories = stats.get('categories', {})
            if categories:
                fig = px.pie(
                    values=list(categories.values()),
                    names=list(categories.keys()),
                    title="Documents par catégorie"
                )
                st.plotly_chart(fig)
            else:
                st.info("Aucune donnée de catégorie disponible")
            
            # Liste des topics
            st.subheader("Topics Disponibles")
            topics = stats.get('topics', {})
            if topics:
                topics_df = pd.DataFrame([
                    {'Topic': k, 'Documents': v} 
                    for k, v in sorted(topics.items(), key=lambda x: x[1], reverse=True)
                ])
                st.dataframe(topics_df, use_container_width=True)
        
        with tab2:
            st.subheader("🔍 Recherche dans la Base")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input("Recherche", placeholder="Ex: index lent, sécurité password, backup RMAN...")
            with col2:
                n_results = st.number_input("Nombre résultats", 1, 20, 5)
            
            # Obtenir les catégories
            stats = rag.get_collection_stats()
            category_options = ["Toutes"] + list(stats.get('categories', {}).keys())
            
            category_filter = st.selectbox(
                "Filtrer par catégorie",
                category_options
            )
            
            if st.button("🔍 Rechercher", type="primary"):
                if search_query:
                    with st.spinner("Recherche en cours..."):
                        if category_filter == "Toutes":
                            results = rag.retrieve_context(search_query, n_results)
                        else:
                            results = rag.search_by_category(category_filter, search_query, n_results)
                        
                        if results:
                            st.success(f"✅ {len(results)} documents trouvés")
                            
                            for i, doc in enumerate(results, 1):
                                with st.expander(f"📄 Document {i}: {doc.get('metadata', {}).get('topic', 'Sans titre')}", expanded=(i==1)):
                                    st.write(f"**Catégorie:** {doc.get('metadata', {}).get('category', 'N/A')}")
                                    st.write(f"**Sévérité:** {doc.get('metadata', {}).get('severity', 'N/A')}")
                                    if doc.get('distance'):
                                        st.write(f"**Pertinence:** {1 - doc['distance']:.2%}")
                                    st.markdown("---")
                                    if doc.get('content'):
                                        st.markdown(doc['content'][:1000] + ("..." if len(doc['content']) > 1000 else ""))
                        else:
                            st.warning("⚠️ Aucun document trouvé")
        
        with tab3:
            st.subheader("➕ Ajouter un Document Personnalisé")
            
            with st.form("add_document"):
                new_content = st.text_area("Contenu", height=200, placeholder="Entrez le contenu du document...")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_category = st.selectbox("Catégorie", ["security", "performance", "backup", "monitoring", "troubleshooting", "custom"])
                with col2:
                    new_topic = st.text_input("Topic", placeholder="Ex: custom_backup_procedure")
                
                new_severity = st.select_slider("Sévérité", ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
                
                submitted = st.form_submit_button("➕ Ajouter Document")
                
                if submitted:
                    if new_content and new_topic:
                        success = rag.add_custom_document(
                            content=new_content,
                            category=new_category,
                            topic=new_topic,
                            metadata={'severity': new_severity}
                        )
                        
                        if success:
                            st.success("✅ Document ajouté avec succès!")
                            # Mettre à jour les stats
                            st.session_state.rag_stats = rag.get_collection_stats()
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de l'ajout")
                    else:
                        st.warning("⚠️ Veuillez remplir tous les champs")
        
        with tab4:
            st.subheader("🧪 Tests de Récupération")
            
            if st.button("🧪 Lancer Tests Automatiques"):
                with st.spinner("Tests en cours..."):
                    test_results = rag.test_retrieval()
                    
                    for query, result in test_results.items():
                        with st.expander(f"Test: '{query}'"):
                            st.write(f"**Documents trouvés:** {result['found']}")
                            st.write(f"**Topics:** {', '.join(result['top_topics'])}")
                            if result['relevance']:
                                st.write(f"**Scores de pertinence:** {[f'{r:.2%}' for r in result['relevance']]}")
    
    def chatbot_page(self):
        """Chatbot amélioré avec historique complet et RAG"""
        st.title("🤖 Assistant Oracle Expert ")
        st.caption(f"Powered by {self.model_name.upper()} - Réponses enrichies par Base de Connaissances")
        
        # Initialiser l'historique
        if "phi_chat_history" not in st.session_state:
            st.session_state.phi_chat_history = [
                {
                    "role": "assistant",
                    "content": f"""👋 Bonjour! Je suis votre expert Oracle IA ({self.model_name}) .

**Mes spécialités :**
• 🔍 Audit de sécurité avancé avec références documentaires
• ⚡ Optimisation SQL approfondie avec meilleures pratiques  
• 💾 Stratégies de sauvegarde RMAN enrichies
• 📚 Recherche dans la base de connaissances
• 📊 Monitoring et performances
• 🛠️ Dépannage technique avec solutions documentées

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
                "Recherche dans base de connaissances"
            ]
            
            for q in quick_questions:
                if st.button(q, key=f"quick_{q}", use_container_width=True):
                    st.session_state.phi_chat_history.append({"role": "user", "content": q})
                    self._generate_detailed_chat_response(q)
                    st.rerun()
    
    def _generate_detailed_chat_response(self, prompt):
        """Génère une réponse de chat AVEC contexte RAG"""
        with st.chat_message("assistant"):
            with st.spinner("💭 Analyse en cours..."):
                try:
                    # Récupérer RAG si disponible
                    rag = st.session_state.get('rag_integration')
                    
                    if rag and self.llm_engine:
                        # Utiliser RAG pour enrichir la réponse
                        response = rag.enhanced_llm_query(prompt)
                        
                        # Afficher les documents sources utilisés
                        context_docs = rag.retrieve_context(prompt, n_results=2)
                        if context_docs:
                            with st.expander("📚 Sources utilisées"):
                                for i, doc in enumerate(context_docs, 1):
                                    st.caption(f"{i}. {doc.get('metadata', {}).get('category', 'N/A')} / {doc.get('metadata', {}).get('topic', 'Sans titre')}")
                        
                        formatted_response = self._format_chat_response(response, prompt)
                        st.markdown(formatted_response)
                        st.session_state.phi_chat_history.append(
                            {"role": "assistant", "content": formatted_response}
                        )
                        
                    elif self.llm_engine:
                        # LLM sans RAG (fallback)
                        response = self.llm_engine.chat_response(prompt, "")
                        
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
        return response
    
    def _get_fallback_response(self, prompt):
        """Retourne une réponse de secours"""
        return f"""⚠️ Réponse limitée (LLM/RAG non disponible).

**Votre question:** {prompt}

**Suggestions:**
1. Vérifiez qu'Ollama est en cours d'exécution
2. Installez le modèle Phi: `ollama pull phi`
3. Redémarrez l'application

Pour des réponses complètes avec RAG, assurez-vous que:
- Ollama est en cours d'exécution
- ChromaDB est installé et initialisé
- La base de connaissances est chargée"""
    
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
    
    def run(self):
        """Lance le dashboard avec RAG - méthode à appeler depuis app_phi.py"""
        page = self.setup_sidebar()
        
        # Router vers les pages
        if page == "home":
            self.home_page()
        elif page == "security":
            self.security_page()
        elif page == "performance":
            self.performance_page()
        elif page == "backup":
            self.backup_page()
        elif page == "chat":
            self.chatbot_page()
        elif page == "knowledge_base":
            self.knowledge_base_page()