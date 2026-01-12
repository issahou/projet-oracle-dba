# src/llm_engine_phi.py - 
import yaml
import json
import requests
from typing import Dict, Any, Optional, Tuple
import os
import re

class LLMEnginePhi:
    def __init__(self, model: str = "phi:latest", base_url: str = "http://localhost:11434"):
        """
        LLM Engine optimisé pour Phi avec réponses détaillées
        """
        self.model = model
        self.base_url = base_url
        self.prompts = self._load_prompts()
        
    def _load_prompts(self) -> Dict:
        """Charge les prompts détaillés pour réponses techniques"""
        prompts_path = 'data/prompts.yaml'
        
        # Prompts détaillés pour réponses techniques complètes
        default_prompts = {
            "security_assessment": """Tu es un expert en sécurité Oracle certifié avec 10 ans d'expérience.

Configuration à analyser: {config}

Fournis une analyse COMPLÈTE au format JSON:
{{
    "score": 0-100,
    "risks": [
        {{
            "type": "TYPE_RISQUE",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "description": "Description technique détaillée",
            "details": "Explications techniques avec références Oracle",
            "recommendation": "Solution spécifique avec commandes SQL à exécuter"
        }}
    ],
    "recommendations": [
        {{
            "priority": "CRITICAL|HIGH|MEDIUM|LOW",
            "action": "Action concrète avec étapes détaillées",
            "commands": ["Commande SQL spécifique 1", "Commande SQL spécifique 2"]
        }}
    ]
}}

Inclus des exemples concrets et commandes SQL/PLSQL.""",
            
            "query_analysis": """Tu es un expert en optimisation SQL Oracle, spécialiste des performances.

REQUÊTE À ANALYSER: {sql_query}
PLAN D'EXÉCUTION: {execution_plan}

Fournis une analyse TECHNIQUE DÉTAILLÉE incluant:

1. DIAGNOSTIC COMPLET:
   - Problèmes identifiés (scans complets, jointures hash, opérations coûteuses)
   - Statistiques à vérifier avec: SELECT * FROM V$SQL WHERE sql_id = '...'
   - Coût estimé et impact sur les ressources

2. RECOMMANDATIONS D'INDEXATION:
   - Index recommandés avec syntaxe EXACTE:
     CREATE INDEX nom_index ON table(colonne) TABLESPACE ts_data;
   - Index composites si nécessaire
   - Partitionnement à considérer

3. VERSION OPTIMISÉE DE LA REQUÊTE:
   - Code SQL complet avant/après
   - Utilisation de hints si pertinent: /*+ INDEX(table index_name) */
   - Réécriture avec CTE, sous-requêtes optimisées

4. VÉRIFICATIONS À EFFECTUER:
   - Commandes pour vérifier les stats: EXEC DBMS_STATS.GATHER_TABLE_STATS('SCHEMA', 'TABLE');
   - Analyse du plan avec: EXPLAIN PLAN FOR ... SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
   - Monitoring avec: SELECT * FROM V$SQL_MONITOR WHERE sql_id = '...';

5. GAIN DE PERFORMANCE ESTIMÉ: 50-80%

Donne des exemples concrets et des commandes exécutables.""",
            
            "backup_recommendation": """Expert en sauvegarde Oracle RMAN avec expérience production.

EXIGENCES:
- RPO: {rpo}
- RTO: {rto}
- Taille des données: {data_size}
- Criticité: {criticality}

Fournis une stratégie COMPLÈTE au format JSON:
{{
    "strategy": {{
        "type": "FULL|INCREMENTAL_LEVEL_1|DIFFERENTIAL",
        "frequency": "HOURLY|DAILY|WEEKLY",
        "retention_days": 30,
        "storage": "DISK_ASM|NFS|CLOUD",
        "estimated_cost": "coût estimé",
        "advantages": "liste des avantages",
        "limitations": "limitations à connaître"
    }},
    "rman_script": "Script RMAN COMPLET avec commentaires:
RUN {{
    -- Configuration
    CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF 7 DAYS;
    CONFIGURE CONTROLFILE AUTOBACKUP ON;
    
    -- Sauvegarde principale
    ALLOCATE CHANNEL ch1 TYPE DISK;
    BACKUP AS COMPRESSED BACKUPSET
      DATABASE
      PLUS ARCHIVELOG
      DELETE INPUT;
    
    -- Vérification
    BACKUP VALIDATE DATABASE;
    
    -- Rapport
    REPORT OBSOLETE;
    LIST BACKUP SUMMARY;
    
    RELEASE CHANNEL ch1;
}}",
    "implementation_steps": [
        "Étape 1: Vérifier l'espace disque avec: SELECT * FROM V$RECOVERY_FILE_DEST;",
        "Étape 2: Configurer les paramètres: ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = 100G;",
        "Étape 3: Tester la restauration sur environnement de test"
    ]
}}

Inclus des commandes de monitoring: LIST BACKUP, REPORT OBSOLETE, CROSSCHECK BACKUP.""",
            
            "anomaly_detection": """Expert en monitoring et détection d'anomalies Oracle.

ENTRÉE DE LOG: {log_entry}
CONTEXTE: {context}

Fournis une analyse DÉTAILLÉE avec:

1. CLASSIFICATION: NORMAL|SUSPECT|CRITICAL
2. JUSTIFICATION TECHNIQUE APPROFONDIE:
   - Pattern détecté et sa signification
   - Codes d'erreur Oracle et leur explication
   - Impact potentiel sur la base de données
3. INVESTIGATION REQUISE:
   - Requêtes de diagnostic à exécuter
   - Alertes à vérifier dans Enterprise Manager
   - Fichiers logs additionnels à examiner
4. ACTIONS IMMÉDIATES:
   - Commandes à exécuter pour investigation
   - Correctifs si nécessaire
   - Monitoring à mettre en place
5. DOCUMENTATION:
   - Notes Oracle MOS pertinentes
   - Références aux manuels Oracle
   - Scripts de diagnostic""",
            
            "chatbot_general": """Tu es un DBA Oracle SENIOR avec 15 ans d'expérience en production.

QUESTION DE L'UTILISATEUR: {query}
=== EXEMPLES DE BONNES RÉPONSES ===

Q: "Comment améliorer la sécurité ?"
R: "Pour améliorer la sécurité Oracle:
1. Activer l'audit: ALTER SYSTEM SET AUDIT_TRAIL='DB' SCOPE=SPFILE;
2. Mots de passe forts: CREATE PROFILE secure LIMIT PASSWORD_LIFE_TIME 90 PASSWORD_REUSE_MAX 5 FAILED_LOGIN_ATTEMPTS 3;
3. Révoquer privilèges inutiles: REVOKE DBA FROM app_user;"

Q: "Comment optimiser une requête ?"
R: "Pour optimiser:
1. Créer un index composite: CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
2. Mettre à jour les statistiques: EXEC DBMS_STATS.GATHER_TABLE_STATS('SCHEMA','ORDERS');
3. Analyser le plan: EXPLAIN PLAN FOR SELECT ...; puis SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);"

=== FIN DES EXEMPLES ===

Maintenant réponds à: {query}
."""
        }
        
        if os.path.exists(prompts_path):
            try:
                with open(prompts_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
                    if loaded:
                        # Fusionner les prompts
                        for key in loaded:
                            if key in default_prompts:
                                default_prompts[key] = loaded[key]
            except Exception as e:
                print(f"⚠️ Erreur chargement prompts YAML: {e}")
                print("✅ Utilisation des prompts détaillés par défaut")
        
        return default_prompts
    
    def generate(self, prompt_key: str, 
                 variables: Optional[Dict] = None,
                 max_tokens: int = 1000) -> str:
        """
        Génère une réponse détaillée avec Phi
        """
        template = self.prompts.get(prompt_key, "")
        if not template:
            return f"Prompt '{prompt_key}' non trouvé"
        
        # Remplacer les variables
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                template = template.replace(placeholder, str(value))
        
        # Ne pas trop limiter la taille du prompt pour garder les instructions
        prompt = template[:2000]  # Limite raisonnable mais pas trop restrictive
        
        try:
            # Vérifier d'abord si Ollama est disponible
            health_check = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if health_check.status_code != 200:
                return f"❌ Ollama non disponible: {health_check.status_code}"
            
            # Appel à l'API Ollama avec paramètres optimisés pour réponses détaillées
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,  # Plus créatif pour réponses détaillées
                        "top_p": 0.92,
                        "num_predict": max_tokens,
                        "num_ctx": 2048,  # Contexte plus large
                        "repeat_penalty": 1.1,
                        "top_k": 50,
                        "mirostat": 2,  # Meilleure cohérence
                        "mirostat_tau": 5.0,
                        "mirostat_eta": 0.1
                    }
                },
                timeout=600  # Timeout plus long pour réponses détaillées
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "Pas de réponse")
                
                # Nettoyer la réponse si nécessaire
                if response_text.startswith("Sure") or response_text.startswith("Okay"):
                    # Enlever les préambules automatiques
                    lines = response_text.split('\n')
                    response_text = '\n'.join([line for line in lines if not line.startswith(('Sure', 'Okay', 'Here'))])
                
                return response_text
            else:
                error_msg = f"❌ Erreur API: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f" - {error_details}"
                except:
                    error_msg += f" - {response.text[:200]}"
                return error_msg
                
        except requests.exceptions.Timeout:
            return f"❌ Timeout - Le modèle {self.model} ne répond pas dans les 60 secondes"
        except requests.exceptions.ConnectionError:
            return f"❌ Impossible de se connecter à Ollama. Assurez-vous qu'il tourne sur {self.base_url}"
        except Exception as e:
            return f"❌ Erreur: {str(e)[:150]}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """Teste la connexion à Ollama et au modèle"""
        try:
            # Test de connexion de base
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                return False, f"❌ Ollama API: {response.status_code}"
            
            # Vérifier si le modèle est disponible (avec correspondance partielle)
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Chercher une correspondance partielle (phi, phi:latest, etc.)
            model_found = False
            model_detected = None
            
            for name in model_names:
                if self.model in name or name in self.model:
                    model_found = True
                    model_detected = name
                    break
            
            if not model_found:
                available = ", ".join(model_names) if model_names else "aucun"
                return False, f"❌ Modèle '{self.model}' non trouvé. Disponibles: {available}"
            
            # Test rapide du modèle
            test_response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_detected or self.model,
                    "prompt": "Test de connexion Oracle DBA",
                    "stream": False,
                    "options": {"num_predict": 20}
                },
                timeout=15
            )
            
            if test_response.status_code == 200:
                model_name = model_detected or self.model
                return True, f"✅ Modèle '{model_name}' prêt et fonctionnel"
            else:
                return False, f"❌ Test modèle échoué: {test_response.status_code}"
                
        except Exception as e:
            return False, f"❌ Erreur connexion: {str(e)}"
    
    def assess_security(self, config: Dict) -> Dict:
        """Évalue la configuration de sécurité avec analyse détaillée"""
        # Convertir la configuration en format lisible
        if isinstance(config, dict):
            config_str = json.dumps(config, ensure_ascii=False, indent=2)
        else:
            config_str = str(config)
        
        response = self.generate(
            "security_assessment",
            variables={"config": config_str},
            max_tokens=800  # Plus de tokens pour analyse détaillée
        )
        
        # Essayer d'extraire et parser le JSON
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            try:
                # Essayer de parser directement
                return json.loads(response)
            except:
                # Essayer d'extraire le JSON du texte
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
        
        # Fallback si JSON parsing échoue
        return {
            "score": 85,
            "risks": [{
                "type": "ANALYSIS_ERROR",
                "severity": "MEDIUM",
                "description": f"Erreur d'analyse LLM: {response[:200] if isinstance(response, str) else 'Réponse invalide'}",
                "details": "L'analyse LLM n'a pas retourné un JSON valide",
                "recommendation": "Vérifier la configuration et réessayer"
            }],
            "recommendations": [
                {"priority": "MEDIUM", "action": "Vérifier la connexion au modèle LLM"}
            ]
        }
    
    def chat_response(self, query: str, history: str = "") -> str:
        """Réponse de chat détaillée"""
        return self.generate(
            "chatbot_general",
            variables={
                "query": query[:1000],  # Limite plus large pour questions complexes
                "history": history[:2000]  # Historique plus long
            },
            max_tokens=1200  # Réponses longues et détaillées
        )
    
    def analyze_query(self, sql_query: str, execution_plan: str = "") -> str:
        """Analyse détaillée d'une requête SQL"""
        return self.generate(
            "query_analysis",
            variables={
                "sql_query": sql_query[:1500],
                "execution_plan": execution_plan[:2000]
            },
            max_tokens=1000
        )
    
    def get_backup_strategy(self, requirements: Dict) -> Dict:
        """Génère une stratégie de sauvegarde détaillée"""
        response = self.generate(
            "backup_recommendation",
            variables={
                "rpo": requirements.get('rpo', '24h'),
                "rto": requirements.get('rto', '4h'),
                "data_size": requirements.get('data_size', '100GB'),
                "criticality": requirements.get('criticality', 'HIGH')
            },
            max_tokens=800
        )
        
        # Essayer d'extraire le JSON
        if isinstance(response, str):
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        # Fallback
        return {
            "strategy": {
                "type": "FULL",
                "frequency": "DAILY",
                "retention_days": 30,
                "storage": "DISK",
                "estimated_cost": "Variable selon infrastructure",
                "advantages": "Sauvegarde complète, restauration simple",
                "limitations": "Temps de sauvegarde long, espace disque important"
            },
            "rman_script": """RUN {
  ALLOCATE CHANNEL ch1 TYPE DISK;
  BACKUP DATABASE PLUS ARCHIVELOG;
  BACKUP CURRENT CONTROLFILE;
  RELEASE CHANNEL ch1;
}""",
            "implementation_steps": [
                "1. Vérifier l'espace: SELECT * FROM V$RECOVERY_FILE_DEST;",
                "2. Configurer: ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = 100G;",
                "3. Tester la restauration complète"
            ]
        }
    
    def detect_anomaly(self, log_entry: str, context: str = "") -> Dict:
        """Détecte les anomalies dans les logs"""
        response = self.generate(
            "anomaly_detection",
            variables={
                "log_entry": log_entry[:500],
                "context": context[:1000]
            },
            max_tokens=500
        )
        
        # Classification automatique basée sur les mots-clés
        if isinstance(response, str):
            lower_response = response.lower()
            if any(word in lower_response for word in ["critique", "critical", "attaque", "attack", "intrusion", "breach"]):
                risk_level = "CRITICAL"
            elif any(word in lower_response for word in ["suspect", "suspicious", "anormal", "unusual", "warning"]):
                risk_level = "HIGH"
            else:
                risk_level = "NORMAL"
        else:
            risk_level = "NORMAL"
        
        return {
            "log": log_entry,
            "analysis": response,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat()
        }