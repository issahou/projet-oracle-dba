# src/data_extractor.py
import cx_Oracle
import pandas as pd
import json
from datetime import datetime
import os
from typing import Dict, List, Union, Optional

class OracleExtractor:
    def __init__(self, username: str, password: str, dsn: str):
        """
        Initialise la connexion à la base de données Oracle
        
        Args:
            username: Nom d'utilisateur Oracle
            password: Mot de passe Oracle
            dsn: Data Source Name (host:port/service_name)
        """
        try:
            self.connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn=dsn,
                encoding="UTF-8"
            )
            self.cursor = self.connection.cursor()
            print(f"✅ Connexion établie à Oracle: {dsn}")
        except cx_Oracle.Error as e:
            print(f"❌ Erreur de connexion Oracle: {e}")
            raise
    
    def extract_audit_logs(self, days: int = 30) -> pd.DataFrame:
        """
        Extrait les logs d'audit depuis AUD$
        
        Args:
            days: Nombre de jours à remonter
            
        Returns:
            DataFrame des logs d'audit
        """
        try:
            query = f"""
            SELECT USERID, USERHOST, TERMINAL, TIMESTAMP#, 
                   ACTION#, RETURNCODE, OBJ$CREATOR, OBJ$NAME,
                   SESSIONID, ENTRYID, COMMENT$TEXT
            FROM SYS.AUD$
            WHERE TIMESTAMP# > SYSDATE - {days}
            ORDER BY TIMESTAMP# DESC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            df = pd.DataFrame(results, columns=[
                'USERID', 'USERHOST', 'TERMINAL', 'TIMESTAMP',
                'ACTION', 'RETURNCODE', 'OBJECT_OWNER', 'OBJECT_NAME',
                'SESSION_ID', 'ENTRY_ID', 'COMMENT'
            ])
            
            print(f"✅ {len(df)} logs d'audit extraits (derniers {days} jours)")
            return df
            
        except cx_Oracle.Error as e:
            print(f"❌ Erreur lors de l'extraction des logs d'audit: {e}")
            return pd.DataFrame()
    
    def extract_performance_metrics(self) -> Dict[str, pd.DataFrame]:
        """
        Extrait les métriques de performance
        
        Returns:
            Dictionnaire avec différents DataFrames de métriques
        """
        metrics = {}
        
        try:
            # Requêtes lentes
            slow_queries_query = """
                SELECT SQL_ID, SQL_TEXT, EXECUTIONS, ELAPSED_TIME,
                       CPU_TIME, BUFFER_GETS, DISK_READS, ROWS_PROCESSED,
                       FIRST_LOAD_TIME, LAST_LOAD_TIME
                FROM V$SQLSTAT
                WHERE EXECUTIONS > 0 AND ELAPSED_TIME > 1000000  # > 1 seconde
                ORDER BY ELAPSED_TIME DESC
                FETCH FIRST 50 ROWS ONLY
            """
            metrics['slow_queries'] = pd.read_sql(slow_queries_query, self.connection)
            print(f"✅ {len(metrics['slow_queries'])} requêtes lentes extraites")
            
            # Événements système
            system_events_query = """
                SELECT EVENT, TOTAL_WAITS, TIME_WAITED, AVERAGE_WAIT
                FROM V$SYSTEM_EVENT
                ORDER BY TIME_WAITED DESC
            """
            metrics['system_events'] = pd.read_sql(system_events_query, self.connection)
            
            # Statistiques de la base
            db_stats_query = """
                SELECT NAME, VALUE 
                FROM V$SYSSTAT 
                WHERE NAME IN (
                    'user commits', 'user rollbacks', 
                    'physical reads', 'physical writes',
                    'sorts (memory)', 'sorts (disk)'
                )
            """
            metrics['db_statistics'] = pd.read_sql(db_stats_query, self.connection)
            
            return metrics
            
        except cx_Oracle.Error as e:
            print(f"❌ Erreur lors de l'extraction des métriques: {e}")
            return metrics
    
    def extract_security_configuration(self) -> Dict[str, pd.DataFrame]:
        """
        Extrait la configuration de sécurité
        
        Returns:
            Dictionnaire avec configurations de sécurité
        """
        security_data = {}
        
        try:
            # Utilisateurs
            users_query = """
                SELECT USERNAME, ACCOUNT_STATUS, CREATED, 
                       LOCK_DATE, EXPIRY_DATE, PROFILE
                FROM DBA_USERS
                ORDER BY USERNAME
            """
            security_data['users'] = pd.read_sql(users_query, self.connection)
            print(f"✅ {len(security_data['users'])} utilisateurs extraits")
            
            # Rôles
            roles_query = """
                SELECT ROLE, PASSWORD_REQUIRED, AUTHENTICATION_TYPE
                FROM DBA_ROLES
                ORDER BY ROLE
            """
            security_data['roles'] = pd.read_sql(roles_query, self.connection)
            
            # Privilèges système
            sys_privs_query = """
                SELECT GRANTEE, PRIVILEGE, ADMIN_OPTION
                FROM DBA_SYS_PRIVS
                ORDER BY GRANTEE
            """
            security_data['system_privileges'] = pd.read_sql(sys_privs_query, self.connection)
            
            # Privilèges objet
            obj_privs_query = """
                SELECT GRANTEE, OWNER, TABLE_NAME, PRIVILEGE, GRANTABLE
                FROM DBA_TAB_PRIVS
                WHERE GRANTEE NOT IN ('PUBLIC')
                ORDER BY GRANTEE
            """
            security_data['object_privileges'] = pd.read_sql(obj_privs_query, self.connection)
            
            # Profils
            profiles_query = """
                SELECT PROFILE, RESOURCE_NAME, LIMIT
                FROM DBA_PROFILES
                ORDER BY PROFILE, RESOURCE_NAME
            """
            security_data['profiles'] = pd.read_sql(profiles_query, self.connection)
            
            # Audit config
            audit_query = """
                SELECT PARAMETER, VALUE
                FROM DBA_AUDIT_POLICY
                UNION
                SELECT 'AUDIT_TRAIL', VALUE 
                FROM V$PARAMETER 
                WHERE NAME = 'audit_trail'
            """
            security_data['audit_config'] = pd.read_sql(audit_query, self.connection)
            
            return security_data
            
        except cx_Oracle.Error as e:
            print(f"❌ Erreur lors de l'extraction de la configuration sécurité: {e}")
            return security_data
    
    def extract_execution_plans(self, sql_ids: List[str] = None) -> Dict[str, str]:
        """
        Extrait les plans d'exécution
        
        Args:
            sql_ids: Liste des SQL_ID à analyser (si None, utilise les requêtes lentes)
            
        Returns:
            Dictionnaire SQL_ID -> plan d'exécution
        """
        plans = {}
        
        try:
            if sql_ids is None:
                # Récupérer les SQL_ID des requêtes lentes
                query = """
                    SELECT SQL_ID 
                    FROM V$SQLSTAT 
                    WHERE ELAPSED_TIME > 1000000 
                    AND ROWNUM <= 10
                """
                self.cursor.execute(query)
                sql_ids = [row[0] for row in self.cursor.fetchall()]
            
            for sql_id in sql_ids:
                plan_query = f"""
                    SELECT PLAN_TABLE_OUTPUT 
                    FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR('{sql_id}'))
                """
                self.cursor.execute(plan_query)
                plan_output = "\n".join([row[0] for row in self.cursor.fetchall()])
                plans[sql_id] = plan_output
            
            print(f"✅ {len(plans)} plans d'exécution extraits")
            return plans
            
        except cx_Oracle.Error as e:
            print(f"❌ Erreur lors de l'extraction des plans d'exécution: {e}")
            return plans
    
    def extract_all_data(self) -> Dict[str, Union[pd.DataFrame, Dict]]:
        """
        Extrait toutes les données en une seule opération
        
        Returns:
            Dictionnaire avec toutes les données extraites
        """
        print("=== Début de l'extraction complète des données ===")
        
        all_data = {
            'audit_logs': self.extract_audit_logs(),
            'performance_metrics': self.extract_performance_metrics(),
            'security_config': self.extract_security_configuration(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Normalisation des données
        all_data['audit_logs'] = self.normalize_data(all_data['audit_logs'], 'audit')
        
        print("=== Extraction terminée ===")
        return all_data
    
    def _map_audit_action(self, action_code: int) -> str:
        """
        Mappe les codes d'action d'audit Oracle en noms lisibles
        
        Args:
            action_code: Code numérique de l'action
            
        Returns:
            Nom de l'action ou code si non trouvé
        """
        action_map = {
            # Connexion/Déconnexion
            100: "LOGON",
            101: "LOGOFF",
            102: "LOGON FAILED",
            
            # Objets de base de données
            1: "CREATE TABLE",
            2: "INSERT",
            3: "SELECT",
            4: "CREATE CLUSTER",
            5: "ALTER CLUSTER",
            6: "UPDATE",
            7: "DELETE",
            8: "DROP CLUSTER",
            9: "CREATE INDEX",
            10: "DROP INDEX",
            11: "ALTER INDEX",
            12: "DROP TABLE",
            13: "CREATE SEQUENCE",
            14: "ALTER SEQUENCE",
            15: "ALTER TABLE",
            16: "DROP SEQUENCE",
            17: "CREATE VIEW",
            18: "DROP VIEW",
            19: "CREATE SYNONYM",
            20: "DROP SYNONYM",
            21: "CREATE DATABASE LINK",
            22: "DROP DATABASE LINK",
            
            # Privilèges
            23: "CREATE ROLE",
            24: "DROP ROLE",
            25: "SET ROLE",
            26: "CREATE USER",
            27: "ALTER USER",
            28: "DROP USER",
            29: "CREATE ROLLBACK SEGMENT",
            30: "ALTER ROLLBACK SEGMENT",
            31: "DROP ROLLBACK SEGMENT",
            
            # Contrôle d'accès
            40: "GRANT",
            41: "REVOKE",
            
            # Audit
            42: "AUDIT",
            43: "NOAUDIT",
            
            # Système
            70: "ALTER DATABASE",
            71: "ALTER SYSTEM",
            72: "CREATE TABLESPACE",
            73: "ALTER TABLESPACE",
            74: "DROP TABLESPACE",
            
            # Rôles et profils
            90: "CREATE PROFILE",
            91: "ALTER PROFILE",
            92: "DROP PROFILE",
        }
        
        return action_map.get(action_code, f"ACTION_{action_code}")
    
    def normalize_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Normalise les données extraites
        
        Args:
            df: DataFrame à normaliser
            data_type: Type de données ('audit', 'performance', 'security')
            
        Returns:
            DataFrame normalisé
        """
        if df.empty:
            return df
        
        # Convertir les timestamps
        timestamp_columns = ['TIMESTAMP', 'CREATED', 'LOCK_DATE', 'EXPIRY_DATE', 
                           'FIRST_LOAD_TIME', 'LAST_LOAD_TIME']
        
        for col in timestamp_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        
        # Conversion en format standard selon le type de données
        if data_type == 'audit':
            if 'ACTION' in df.columns:
                df['ACTION_NAME'] = df['ACTION'].apply(self._map_audit_action)
            
            # Catégoriser les codes de retour
            if 'RETURNCODE' in df.columns:
                def categorize_returncode(code):
                    if code == 0:
                        return "SUCCESS"
                    elif code == 1017:  # Invalid username/password
                        return "AUTH_FAILURE"
                    elif code == 1031:  # Insufficient privileges
                        return "PRIVILEGE_ERROR"
                    else:
                        return f"ERROR_{code}"
                
                df['RETURNCODE_CATEGORY'] = df['RETURNCODE'].apply(categorize_returncode)
        
        elif data_type == 'performance':
            # Convertir les temps de microsecondes en secondes
            time_columns = ['ELAPSED_TIME', 'CPU_TIME', 'TIME_WAITED']
            for col in time_columns:
                if col in df.columns:
                    df[f'{col}_SECONDS'] = df[col] / 1000000  # Convertir en secondes
        
        elif data_type == 'security':
            # Normaliser les statuts de compte
            if 'ACCOUNT_STATUS' in df.columns:
                status_mapping = {
                    'OPEN': 'ACTIVE',
                    'LOCKED': 'LOCKED',
                    'EXPIRED': 'EXPIRED',
                    'EXPIRED(GRACE)': 'EXPIRED_GRACE'
                }
                df['ACCOUNT_STATUS_NORMALIZED'] = df['ACCOUNT_STATUS'].map(
                    lambda x: status_mapping.get(x, x)
                )
        
        return df
    
    def export_data(self, df: pd.DataFrame, filename: str, format: str = 'csv') -> str:
        """
        Exporte les données normalisées
        
        Args:
            df: DataFrame à exporter
            filename: Nom du fichier (sans extension)
            format: Format d'export ('csv' ou 'json')
            
        Returns:
            Chemin du fichier exporté
        """
        os.makedirs('data/extracted', exist_ok=True)
        
        # Ajouter l'extension si absente
        if not any(filename.endswith(ext) for ext in ['.csv', '.json']):
            filename = f"{filename}.{format}"
        
        path = f'data/extracted/{filename}'
        
        try:
            if format == 'csv':
                df.to_csv(path, index=False, encoding='utf-8')
                print(f"✅ Données exportées en CSV: {path}")
                
            elif format == 'json':
                # Convertir les timestamps pour JSON
                df_copy = df.copy()
                for col in df_copy.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                        df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                df_copy.to_json(path, orient='records', date_format='iso', indent=2)
                print(f"✅ Données exportées en JSON: {path}")  # <-- CORRECTION ICI
            
            return path
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
            return ""
    
    def export_all_data(self, data_dict: Dict, prefix: str = "oracle_data"):
        """
        Exporte toutes les données extraites
        
        Args:
            data_dict: Dictionnaire de données
            prefix: Préfixe pour les noms de fichiers
        """
        print(f"=== Export des données avec préfixe: {prefix} ===")
        
        exported_files = []
        
        # Exporter les logs d'audit
        if 'audit_logs' in data_dict and not data_dict['audit_logs'].empty:
            path = self.export_data(data_dict['audit_logs'], f"{prefix}_audit_logs.csv")
            exported_files.append(path)
        
        # Exporter les métriques de performance
        if 'performance_metrics' in data_dict:
            for metric_name, metric_df in data_dict['performance_metrics'].items():
                if not metric_df.empty:
                    path = self.export_data(metric_df, f"{prefix}_{metric_name}.csv")
                    exported_files.append(path)
        
        # Exporter la configuration sécurité
        if 'security_config' in data_dict:
            for config_name, config_df in data_dict['security_config'].items():
                if not config_df.empty:
                    path = self.export_data(config_df, f"{prefix}_{config_name}.csv")
                    exported_files.append(path)
        
        # Exporter un résumé JSON
        summary = {
            'export_timestamp': datetime.now().isoformat(),
            'files_exported': exported_files,
            'data_summary': {
                'audit_logs_count': len(data_dict.get('audit_logs', pd.DataFrame())),
                'performance_metrics_count': sum(
                    len(df) for df in data_dict.get('performance_metrics', {}).values()
                ),
                'security_config_items': sum(
                    len(df) for df in data_dict.get('security_config', {}).values()
                )
            }
        }
        
        summary_path = f'data/extracted/{prefix}_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Résumé exporté: {summary_path}")
        print(f"✅ {len(exported_files)} fichiers exportés au total")
        
        return exported_files
    
    def get_database_info(self) -> Dict:
        """
        Récupère les informations générales de la base de données
        
        Returns:
            Dictionnaire d'informations
        """
        try:
            info = {}
            
            # Version Oracle
            version_query = "SELECT * FROM V$VERSION"
            self.cursor.execute(version_query)
            info['version'] = [row[0] for row in self.cursor.fetchall()]
            
            # Paramètres
            params_query = """
                SELECT NAME, VALUE, DISPLAY_VALUE 
                FROM V$PARAMETER 
                WHERE NAME IN (
                    'db_name', 'db_unique_name', 'compatible',
                    'sga_target', 'pga_aggregate_target'
                )
            """
            self.cursor.execute(params_query)
            info['parameters'] = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # Espace disque
            tablespace_query = """
                SELECT TABLESPACE_NAME, BYTES/1024/1024 as SIZE_MB, 
                       MAXBYTES/1024/1024 as MAX_SIZE_MB
                FROM DBA_DATA_FILES
            """
            info['tablespaces'] = pd.read_sql(tablespace_query, self.connection)
            
            return info
            
        except cx_Oracle.Error as e:
            print(f"❌ Erreur lors de la récupération des infos DB: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à la base de données
        
        Returns:
            True si la connexion est fonctionnelle
        """
        try:
            self.cursor.execute("SELECT 1 FROM DUAL")
            result = self.cursor.fetchone()
            return result[0] == 1
        except:
            return False
    
    def close(self):
        """
        Ferme la connexion à la base de données
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("✅ Connexion Oracle fermée")
        except:
            print("⚠️  Erreur lors de la fermeture de la connexion")
    
    def __del__(self):
        """Destructeur pour fermer la connexion"""
        self.close()


# Fonctions utilitaires additionnelles

def create_mock_data() -> Dict:
    """
    Crée des données de test pour le développement
    """
    from datetime import datetime, timedelta
    
    print("Création de données de test...")
    
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


# ... (le code existant jusqu'à la fin de la fonction create_mock_data)

class MockExtractor:
    def normalize_data(self, df, data_type):
        return df
    
    def export_data(self, df, filename, format='csv'):
        os.makedirs('data/extracted', exist_ok=True)
        path = f'data/extracted/{filename}'
        df.to_csv(path, index=False)
        return path

if __name__ == "__main__":
    # Exemple d'utilisation
    print("=== Test du module data_extractor ===")
    
    # Créer des données de test
    test_data = create_mock_data()
    
    extractor = MockExtractor()
    
    # Exporter les données de test
    extractor.export_data(test_data['audit_logs'], 'test_audit_logs.csv')
    
    print("✅ Test terminé. Données dans data/extracted/")