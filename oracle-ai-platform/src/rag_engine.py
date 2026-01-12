# src/rag_engine.py - Configuration ChromaDB COMPLÈTE CORRIGÉE
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path

class OracleRAGEngine:
    """
    Moteur RAG (Retrieval-Augmented Generation) pour Oracle AI Platform
    Utilise ChromaDB (gratuit, local) pour stocker la base de connaissances Oracle
    """
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        Initialise le moteur RAG avec ChromaDB
        
        Args:
            persist_directory: Dossier de persistance ChromaDB
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        print(f"🔧 Initialisation RAG Engine...")
        
        # Initialiser ChromaDB avec persistance
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Utiliser SentenceTransformer (GRATUIT, local, pas d'API)
        print("📦 Chargement du modèle d'embedding...")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # Modèle léger et performant
        )
        
        # Créer/récupérer la collection Oracle
        self.collection = self._get_or_create_collection()
        
        print(f"✅ RAG Engine initialisé avec {self.collection.count()} documents")
    
    def _get_or_create_collection(self):
        """Récupère ou crée la collection Oracle"""
        try:
            # Essayer de récupérer la collection existante
            collection = self.client.get_collection(
                name="oracle_knowledge_base",
                embedding_function=self.embedding_function
            )
            print(f"📚 Collection existante chargée: {collection.count()} documents")
            
            # Si la collection est vide, charger les documents
            if collection.count() == 0:
                print("⚠️ Collection vide - Chargement des documents initiaux...")
                self._load_initial_documents(collection)
            
        except Exception as e:
            print(f"🆕 Création nouvelle collection (raison: {e})")
            # Créer une nouvelle collection
            collection = self.client.create_collection(
                name="oracle_knowledge_base",
                embedding_function=self.embedding_function,
                metadata={"description": "Oracle Database best practices and documentation"}
            )
            
            # Charger les documents initiaux
            self._load_initial_documents(collection)
        
        return collection
    
    def _load_initial_documents(self, collection):
        """Charge les 15 documents Oracle de base"""
        print("📖 Chargement des documents Oracle...")
        
        # Documents Oracle Best Practices
        oracle_docs = self._get_oracle_knowledge_base()
        
        documents = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(oracle_docs):
            documents.append(doc['content'])
            metadatas.append({
                'category': doc['category'],
                'topic': doc['topic'],
                'severity': doc.get('severity', 'INFO'),
                'source': doc.get('source', 'oracle_internal')
            })
            ids.append(f"oracle_doc_{i}")
        
        try:
            # Vérifier si des documents existent déjà
            try:
                existing = collection.get(ids=ids)
                if existing['ids']:
                    print(f"📚 Documents existants déjà chargés: {len(existing['ids'])}")
                    return
            except:
                pass  # Aucun document existant, continuer
            
            # Ajouter à la collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ {len(documents)} documents Oracle chargés dans ChromaDB")
        except Exception as e:
            print(f"❌ Erreur chargement documents: {e}")
    
    def _get_oracle_knowledge_base(self) -> List[Dict]:
        """
        Retourne la base de connaissances Oracle (15 documents)
        Organisée par catégories : Sécurité, Performance, Backup, Anomalies, Monitoring
        """
        return [
            # SÉCURITÉ (3 docs)
            {
                'category': 'security',
                'topic': 'password_policy',
                'severity': 'CRITICAL',
                'content': """ORACLE BEST PRACTICE: Password Policy Configuration

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

Références: Oracle Database Security Guide 19c, Section 5.3"""
            },
            {
                'category': 'security',
                'topic': 'least_privilege',
                'severity': 'HIGH',
                'content': """ORACLE BEST PRACTICE: Principe du Moindre Privilège

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

Références: Oracle Database Security Guide, Chapitres 4-6"""
            },
            {
                'category': 'security',
                'topic': 'audit_configuration',
                'severity': 'HIGH',
                'content': """ORACLE BEST PRACTICE: Configuration de l'Audit

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

Références: Oracle Security Guide, Chapter 27"""
            },
            
            # PERFORMANCE (4 docs)
            {
                'category': 'performance',
                'topic': 'index_strategy',
                'severity': 'HIGH',
                'content': """ORACLE BEST PRACTICE: Stratégie d'Indexation

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

Références: Performance Tuning Guide, Chapter 5"""
            },
            {
                'category': 'performance',
                'topic': 'sql_hints',
                'severity': 'MEDIUM',
                'content': """ORACLE BEST PRACTICE: Hints SQL

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

Références: SQL Tuning Guide, Chapter 19"""
            },
            {
                'category': 'performance',
                'topic': 'query_rewrite',
                'severity': 'MEDIUM',
                'content': """ORACLE BEST PRACTICE: Réécriture Requêtes

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

Références: SQL Tuning Guide, Chapter 13"""
            },
            {
                'category': 'performance',
                'topic': 'statistics_management',
                'severity': 'HIGH',
                'content': """ORACLE BEST PRACTICE: Gestion Statistiques

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

Références: Performance Tuning Guide, Chapter 13"""
            },
            
            # BACKUP (2 docs)
            {
                'category': 'backup',
                'topic': 'rman_strategy',
                'severity': 'CRITICAL',
                'content': """ORACLE BEST PRACTICE: Stratégie RMAN

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

Références: Backup and Recovery User's Guide"""
            },
            {
                'category': 'backup',
                'topic': 'archivelog_management',
                'severity': 'HIGH',
                'content': """ORACLE BEST PRACTICE: Archive Logs

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

Références: Administrator's Guide, Chapter 11"""
            },
            
            # ANOMALIES (3 docs)
            {
                'category': 'anomaly',
                'topic': 'suspicious_scans',
                'severity': 'CRITICAL',
                'content': """ORACLE ANOMALY: Scans Tables Système

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

Références: Security Guide, Chapter 18"""
            },
            {
                'category': 'anomaly',
                'topic': 'privilege_escalation',
                'severity': 'CRITICAL',
                'content': """ORACLE ANOMALY: Escalade Privilèges

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

Références: Security Guide, Chapters 3-4"""
            },
            {
                'category': 'anomaly',
                'topic': 'ddl_operations',
                'severity': 'HIGH',
                'content': """ORACLE ANOMALY: DDL Suspects

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

Références: Administrator's Guide, Chapter 23"""
            },
            
            # MONITORING (2 docs)
            {
                'category': 'monitoring',
                'topic': 'performance_views',
                'severity': 'MEDIUM',
                'content': """ORACLE BEST PRACTICE: Vues Performance

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

Références: Database Reference Guide"""
            },
            {
                'category': 'monitoring',
                'topic': 'awr_reports',
                'severity': 'HIGH',
                'content': """ORACLE BEST PRACTICE: AWR

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

Références: Performance Tuning Guide, Chapter 8"""
            },
            
            # TROUBLESHOOTING (1 doc)
            {
                'category': 'troubleshooting',
                'topic': 'blocking_sessions',
                'severity': 'HIGH',
                'content': """ORACLE TROUBLESHOOTING: Sessions Bloquantes

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
            }
        ]
    
    # AJOUT DES MÉTHODES MANQUANTES
    def query(self, question: str, n_results: int = 5) -> List[Dict]:
        """
        Recherche de documents pertinents dans la base de connaissances
        
        Args:
            question: Question ou requête de l'utilisateur
            n_results: Nombre de résultats à retourner
            
        Returns:
            Liste de documents pertinents avec métadonnées
        """
        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Formater les résultats
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {str(e)}")
            return []
    
    def add_document(self, content: str, metadata: Dict) -> bool:
        """
        Ajoute un document à la base de connaissances
        
        Args:
            content: Contenu du document
            metadata: Métadonnées (category, topic, severity, source)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Générer un ID unique
            doc_id = f"custom_doc_{self.collection.count() + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            print(f"✅ Document ajouté avec ID: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout du document: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """
        Retourne les statistiques de la collection
        
        Returns:
            Dictionnaire avec statistiques
        """
        try:
            count = self.collection.count()
            
            # Récupérer tous les documents avec métadonnées
            results = self.collection.get(
                include=["metadatas"],
                limit=count if count > 0 else 100
            )
            
            # Compter par catégorie et topic
            categories = {}
            topics = {}
            
            if 'metadatas' in results and results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata:
                        category = metadata.get('category', 'unknown')
                        topic = metadata.get('topic', 'unknown')
                        
                        categories[category] = categories.get(category, 0) + 1
                        topics[topic] = topics.get(topic, 0) + 1
            
            return {
                'total_documents': count,
                'categories': categories,
                'topics': topics,
                'categories_distribution': categories  # Alias pour compatibilité
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération stats: {str(e)}")
            return {
                'total_documents': 0,
                'categories': {},
                'topics': {},
                'categories_distribution': {}
            }
    
    def test_retrieval(self, test_queries: List[str] = None) -> Dict:
        """
        Teste la récupération de documents avec différentes requêtes
        
        Args:
            test_queries: Liste de requêtes de test
            
        Returns:
            Dictionnaire avec résultats des tests
        """
        if test_queries is None:
            test_queries = [
                "index lent performance",
                "sécurité mot de passe Oracle",
                "backup RMAN stratégie",
                "requête SELECT performance",
                "audit Oracle configuration"
            ]
        
        results = {}
        for query in test_queries:
            docs = self.query(query, 3)
            results[query] = {
                'found': len(docs),
                'top_topics': [doc['metadata'].get('topic', 'N/A') for doc in docs[:2]] if docs else [],
                'relevance': [doc.get('similarity_score', 0) for doc in docs[:2]] if docs else []
            }
        
        return results

# Fonction utilitaire pour tester rapidement
def test_rag_engine():
    """Teste le moteur RAG Oracle"""
    print("🧪 Test du RAG Engine Oracle...")
    
    # Initialiser le moteur
    engine = OracleRAGEngine()
    
    # Afficher les statistiques
    stats = engine.get_collection_stats()
    print(f"📊 Statistiques: {stats}")
    
    # Tester quelques requêtes
    test_queries = [
        "Comment configurer une politique de mot de passe Oracle?",
        "Quels sont les meilleurs indexes pour performance?",
        "Comment détecter une attaque sur Oracle?",
        "Backup RMAN best practices",
        "Monitoring sessions bloquantes"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Requête: {query}")
        results = engine.query(query, n_results=3)
        
        print(f"  Résultats trouvés: {len(results)}")
        for i, result in enumerate(results):
            print(f"  {i+1}. [{result['metadata']['category']}] {result['metadata']['topic']} (score: {result['similarity_score']:.3f})")
    
    print("\n✅ Test RAG terminé avec succès!")
    return engine

if __name__ == "__main__":
    test_rag_engine()