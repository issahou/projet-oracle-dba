# src/security_audit.py (version corrigée)
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import os
import html

class SecurityAuditor:
    def __init__(self, llm_engine=None):
        """
        Initialise l'auditeur de sécurité
        
        Args:
            llm_engine: Moteur LLM pour l'analyse (optionnel)
        """
        self.llm = llm_engine
        self.risk_thresholds = {
            'CRITICAL': 20,
            'HIGH': 10,
            'MEDIUM': 5,
            'LOW': 2
        }
        
        # Charger les patterns de sécurité connus
        self.security_patterns = self._load_security_patterns()
    
    def _load_security_patterns(self) -> Dict:
        """Charge les patterns de sécurité connus"""
        return {
            'weak_passwords': [
                'password', '123456', 'oracle', 'admin', 'welcome',
                'qwerty', 'letmein', 'monkey', 'sunshine', 'master'
            ],
            'dangerous_privileges': [
                'DBA', 'SYSDBA', 'SYSOPER', 'GRANT ANY PRIVILEGE',
                'DROP ANY TABLE', 'ALTER ANY TABLE', 'CREATE ANY TABLE',
                'SELECT ANY TABLE', 'INSERT ANY TABLE', 'DELETE ANY TABLE'
            ],
            'insecure_profiles': {
                'FAILED_LOGIN_ATTEMPTS': 'UNLIMITED',
                'PASSWORD_LIFE_TIME': 'UNLIMITED',
                'PASSWORD_REUSE_MAX': 'UNLIMITED',
                'PASSWORD_REUSE_TIME': 'UNLIMITED',
                'PASSWORD_LOCK_TIME': 'UNLIMITED'
            },
            'default_accounts': [
                'SYS', 'SYSTEM', 'DBSNMP', 'OUTLN', 'MGMT_VIEW',
                'ORACLE_OCM', 'XS$NULL', 'SI_INFORMTN_SCHEMA'
            ]
        }
    
    @staticmethod
    def generate_security_examples() -> List[Dict]:
        """
        Génère des exemples de configurations risquées pour few-shot learning
        
        Returns:
            Liste d'exemples de risques de sécurité
        """
        return [
            {
                "risky_config": "GRANT DBA TO PUBLIC;",
                "risk_level": "CRITICAL",
                "explanation": "Donne les privilèges administrateur à tous les utilisateurs",
                "recommendation": "N'accordez DBA qu'aux administrateurs nécessaires. Utilisez des rôles spécifiques."
            },
            {
                "risky_config": "ALTER USER sys IDENTIFIED BY manager;",
                "risk_level": "CRITICAL",
                "explanation": "Mot de passe faible pour le compte SYS (administrateur principal)",
                "recommendation": "Utiliser un mot de passe fort de 15+ caractères avec majuscules, chiffres et caractères spéciaux"
            },
            {
                "risky_config": "ALTER PROFILE DEFAULT LIMIT PASSWORD_REUSE_MAX UNLIMITED;",
                "risk_level": "HIGH",
                "explanation": "Permet la réutilisation illimitée des mots de passe",
                "recommendation": "Limiter la réutilisation des mots de passe (PASSWORD_REUSE_MAX 10, PASSWORD_REUSE_TIME 365)"
            },
            {
                "risky_config": "CREATE USER test IDENTIFIED BY 'password123';",
                "risk_level": "HIGH",
                "explanation": "Mot de passe faible et facile à deviner",
                "recommendation": "Utiliser des mots de passe forts avec majuscules, chiffres et caractères spéciaux"
            },
            {
                "risky_config": "GRANT SELECT ANY TABLE TO dev_user;",
                "risk_level": "MEDIUM",
                "explanation": "Privilège trop large 'SELECT ANY TABLE' pour un utilisateur non-admin",
                "recommendation": "Accorder uniquement les privilèges nécessaires sur des objets spécifiques"
            },
            {
                "risky_config": "AUDIT TRAIL = NONE",
                "risk_level": "HIGH",
                "explanation": "Désactive l'audit de la base de données",
                "recommendation": "Activer l'audit minimal avec 'AUDIT_TRAIL=DB'"
            },
            {
                "risky_config": "REMOTE_OS_AUTHENT = TRUE",
                "risk_level": "HIGH",
                "explanation": "Permet l'authentification à distance non sécurisée",
                "recommendation": "Désactiver cette fonctionnalité (REMOTE_OS_AUTHENT=FALSE)"
            },
            {
                "risky_config": "OS_AUTHENT_PREFIX = '' (vide)",
                "risk_level": "MEDIUM",
                "explanation": "Pas de préfixe pour l'authentification OS, permet des comptes sans mot de passe",
                "recommendation": "Définir un préfixe comme 'OPS$'"
            },
            {
                "risky_config": "UTL_FILE accessible à tous les utilisateurs",
                "risk_level": "HIGH",
                "explanation": "Accès système de fichiers non contrôlé",
                "recommendation": "Restreindre UTL_FILE aux administrateurs seulement"
            },
            {
                "risky_config": "Compte DEFAULT avec privilèges non révoqués",
                "risk_level": "MEDIUM",
                "explanation": "Le compte DEFAULT d'Oracle a souvent des privilèges par défaut",
                "recommendation": "Révoquer les privilèges inutiles du compte DEFAULT"
            }
        ]
    
    def audit_database(self, config_data: Dict) -> Dict:
        """
        Exécute un audit complet de sécurité
        
        Args:
            config_data: Dictionnaire contenant les configurations de sécurité
            
        Returns:
            Rapport d'audit complet
        """
        print("=== Début de l'audit de sécurité Oracle ===")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_info": config_data.get('database_info', {}),
            "score": 100,  # Commence à 100, déduit les points
            "risks": [],
            "recommendations": [],
            "summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Audit des utilisateurs
        if 'users' in config_data:
            print("Audit des utilisateurs...")
            user_risks = self._audit_users(config_data['users'])
            report['risks'].extend(user_risks)
        
        # Audit des rôles
        if 'roles' in config_data:
            print("Audit des rôles...")
            role_risks = self._audit_roles(config_data['roles'])
            report['risks'].extend(role_risks)
        
        # Audit des privilèges système
        if 'system_privileges' in config_data:
            print("Audit des privilèges système...")
            privilege_risks = self._audit_system_privileges(config_data['system_privileges'])
            report['risks'].extend(privilege_risks)
        
        # Audit des privilèges objet
        if 'object_privileges' in config_data:
            print("Audit des privilèges objet...")
            obj_privilege_risks = self._audit_object_privileges(config_data['object_privileges'])
            report['risks'].extend(obj_privilege_risks)
        
        # Audit des profils
        if 'profiles' in config_data:
            print("Audit des profils...")
            profile_risks = self._audit_profiles(config_data['profiles'])
            report['risks'].extend(profile_risks)
        
        # Audit de la configuration audit
        if 'audit_config' in config_data:
            print("Audit de la configuration d'audit...")
            audit_risks = self._audit_audit_config(config_data['audit_config'])
            report['risks'].extend(audit_risks)
        
        # Audit des paramètres de base de données
        if 'database_parameters' in config_data:
            print("Audit des paramètres de base...")
            param_risks = self._audit_database_parameters(config_data['database_parameters'])
            report['risks'].extend(param_risks)
        
        # Calcul du score
        report['score'] = self._calculate_score(report['risks'])
        
        # Génération des recommandations
        report['recommendations'] = self._generate_recommendations(report['risks'])
        
        # Mettre à jour le résumé
        report['summary'] = self._update_summary(report['risks'])
        
        # Si un LLM est disponible, utiliser pour une analyse approfondie
        if self.llm:
            print("Analyse approfondie avec LLM...")
            llm_analysis = self._llm_deep_analysis(config_data, report['risks'])
            report['llm_analysis'] = llm_analysis
        
        print(f"=== Audit terminé. Score: {report['score']}/100 ===")
        return report
    
    def _audit_users(self, users_df: pd.DataFrame) -> List[Dict]:
        """
        Audit des comptes utilisateurs
        
        Args:
            users_df: DataFrame des utilisateurs
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        # Vérifier les comptes par défaut non sécurisés
        for _, user in users_df.iterrows():
            username = user['USERNAME']
            
            # Vérifier les comptes système par défaut
            if username in self.security_patterns['default_accounts']:
                risks.append({
                    'type': 'DEFAULT_ACCOUNT',
                    'severity': 'MEDIUM',
                    'description': f"Compte système par défaut '{username}'",
                    'details': f"Le compte {username} est un compte système Oracle par défaut",
                    'recommendation': f"Changer le mot de passe de {username} et désactiver si non utilisé"
                })
            
            # Vérifier les comptes expirés ou verrouillés
            if user['ACCOUNT_STATUS'] in ['EXPIRED', 'LOCKED']:
                risks.append({
                    'type': 'ACCOUNT_STATUS',
                    'severity': 'MEDIUM',
                    'description': f"Compte '{username}' avec statut '{user['ACCOUNT_STATUS']}'",
                    'details': f"Le compte {username} est {user['ACCOUNT_STATUS'].lower()}",
                    'recommendation': f"Activer ou supprimer le compte {username}"
                })
            
            # Vérifier les comptes sans mot de passe (si cette info est disponible)
            if 'PASSWORD' in user and not user['PASSWORD']:
                risks.append({
                    'type': 'NO_PASSWORD',
                    'severity': 'CRITICAL',
                    'description': f"Compte '{username}' sans mot de passe",
                    'details': f"Le compte {username} peut être connecté sans mot de passe",
                    'recommendation': f"Définir un mot de passe fort pour {username}"
                })
        
        # Vérifier les comptes avec des noms évidents
        weak_usernames = ['test', 'demo', 'temp', 'admin', 'user', 'oracle']
        for _, user in users_df.iterrows():
            username_lower = user['USERNAME'].lower()
            for weak_name in weak_usernames:
                if weak_name in username_lower:
                    risks.append({
                        'type': 'WEAK_USERNAME',
                        'severity': 'LOW',
                        'description': f"Nom d'utilisateur évident: '{user['USERNAME']}'",
                        'details': f"Le nom d'utilisateur contient '{weak_name}' qui est facile à deviner",
                        'recommendation': f"Renommer le compte {user['USERNAME']} avec un nom moins évident"
                    })
                    break
        
        return risks
    
    def _audit_roles(self, roles_df: pd.DataFrame) -> List[Dict]:
        """
        Audit des rôles
        
        Args:
            roles_df: DataFrame des rôles
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        for _, role in roles_df.iterrows():
            role_name = role['ROLE']
            
            # Vérifier les rôles sans mot de passe (si applicable)
            if 'PASSWORD_REQUIRED' in role.columns and role['PASSWORD_REQUIRED'] == 'NO':
                risks.append({
                    'type': 'ROLE_NO_PASSWORD',
                    'severity': 'MEDIUM',
                    'description': f"Rôle '{role_name}' sans mot de passe requis",
                    'details': f"Le rôle {role_name} peut être activé sans mot de passe",
                    'recommendation': f"Ajouter une exigence de mot de passe pour le rôle {role_name}"
                })
        
        return risks
    
    def _audit_system_privileges(self, privs_df: pd.DataFrame) -> List[Dict]:
        """
        Audit des privilèges système
        
        Args:
            privs_df: DataFrame des privilèges système
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        # Regrouper par bénéficiaire
        grouped = privs_df.groupby('GRANTEE')
        
        for grantee, group in grouped:
            privileges = group['PRIVILEGE'].tolist()
            
            # Vérifier les privilèges dangereux
            dangerous_privs = []
            for priv in privileges:
                if priv in self.security_patterns['dangerous_privileges']:
                    dangerous_privs.append(priv)
            
            if dangerous_privs:
                risks.append({
                    'type': 'DANGEROUS_PRIVILEGES',
                    'severity': 'HIGH' if grantee != 'SYS' else 'MEDIUM',
                    'description': f"Privilèges dangereux accordés à '{grantee}'",
                    'details': f"{grantee} a les privilèges: {', '.join(dangerous_privs)}",
                    'recommendation': f"Révoquer les privilèges dangereux non nécessaires de {grantee}"
                })
            
            # Vérifier si PUBLIC a des privilèges
            if grantee == 'PUBLIC' and len(privileges) > 0:
                risks.append({
                    'type': 'PUBLIC_PRIVILEGES',
                    'severity': 'CRITICAL',
                    'description': "Privilèges accordés à PUBLIC",
                    'details': f"PUBLIC a {len(privileges)} privilèges système",
                    'recommendation': "Révoquer tous les privilèges de PUBLIC sauf ceux strictement nécessaires"
                })
        
        return risks
    
    def _audit_object_privileges(self, privs_df: pd.DataFrame) -> List[Dict]:
        """
        Audit des privilèges objet
        
        Args:
            privs_df: DataFrame des privilèges sur objets
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        # Vérifier les privilèges sur objets système
        system_schemas = ['SYS', 'SYSTEM', 'DBSNMP', 'OUTLN']
        for _, priv in privs_df.iterrows():
            if priv['OWNER'] in system_schemas:
                risks.append({
                    'type': 'SYSTEM_OBJECT_ACCESS',
                    'severity': 'HIGH',
                    'description': f"Accès à l'objet système {priv['OWNER']}.{priv['TABLE_NAME']}",
                    'details': f"{priv['GRANTEE']} a le privilège {priv['PRIVILEGE']} sur {priv['OWNER']}.{priv['TABLE_NAME']}",
                    'recommendation': f"Révoquer l'accès non nécessaire à {priv['OWNER']}.{priv['TABLE_NAME']}"
                })
        
        return risks
    
    def _audit_profiles(self, profiles_df: pd.DataFrame) -> List[Dict]:
        """
        Audit des profils de sécurité
        
        Args:
            profiles_df: DataFrame des profils
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        # Regrouper par profil
        grouped = profiles_df.groupby('PROFILE')
        
        for profile_name, group in grouped:
            profile_data = group.set_index('RESOURCE_NAME')['LIMIT'].to_dict()
            
            # Vérifier chaque ressource
            for resource, limit in profile_data.items():
                insecure_value = self.security_patterns['insecure_profiles'].get(resource)
                
                if insecure_value and limit == insecure_value:
                    risks.append({
                        'type': 'INSECURE_PROFILE',
                        'severity': 'MEDIUM',
                        'description': f"Paramètre de sécurité faible dans le profil '{profile_name}'",
                        'details': f"{resource} = {limit} (valeur non sécurisée)",
                        'recommendation': f"Renforcer {resource} dans le profil {profile_name}"
                    })
        
        return risks
    
    def _audit_audit_config(self, audit_df: pd.DataFrame) -> List[Dict]:
        """
        Audit de la configuration d'audit
        
        Args:
            audit_df: DataFrame de configuration d'audit
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        # Vérifier si l'audit est désactivé
        audit_trail = audit_df[audit_df['PARAMETER'] == 'AUDIT_TRAIL']
        if not audit_trail.empty and audit_trail.iloc[0]['VALUE'] == 'NONE':
            risks.append({
                'type': 'AUDIT_DISABLED',
                'severity': 'HIGH',
                'description': "Audit de base de données désactivé",
                'details': "AUDIT_TRAIL = NONE",
                'recommendation': "Activer l'audit (AUDIT_TRAIL=DB)"
            })
        
        return risks
    
    def _audit_database_parameters(self, params_df: pd.DataFrame) -> List[Dict]:
        """
        Audit des paramètres de base de données
        
        Args:
            params_df: DataFrame des paramètres
            
        Returns:
            Liste des risques identifiés
        """
        risks = []
        
        param_map = params_df.set_index('NAME')['VALUE'].to_dict()
        
        # Vérifications spécifiques
        checks = [
            ('REMOTE_OS_AUTHENT', 'FALSE', 'TRUE', 'HIGH', 
             'Authentification OS à distance activée'),
            ('OS_AUTHENT_PREFIX', None, '', 'MEDIUM',
             'Pas de préfixe pour l\'authentification OS'),
            ('REMOTE_LOGIN_PASSWORDFILE', 'NONE', 'EXCLUSIVE', 'MEDIUM',
             'Fichier de mots de passe exclusif'),
            ('UTL_FILE_DIR', None, '*', 'HIGH',
             'Accès UTL_FILE non restreint')
        ]
        
        for param, good_value, bad_value, severity, description in checks:
            if param in param_map:
                current_value = param_map[param]
                if bad_value and current_value == bad_value:
                    risks.append({
                        'type': 'INSECURE_PARAMETER',
                        'severity': severity,
                        'description': description,
                        'details': f"{param} = {current_value}",
                        'recommendation': f"Changer {param} à {good_value if good_value else 'une valeur sécurisée'}"
                    })
        
        return risks
    
    def _calculate_score(self, risks: List[Dict]) -> int:
        """
        Calcule le score de sécurité basé sur les risques
        
        Args:
            risks: Liste des risques
            
        Returns:
            Score de sécurité (0-100)
        """
        score = 100
        
        for risk in risks:
            severity = risk.get('severity', 'MEDIUM')
            deduction = self.risk_thresholds.get(severity, 5)
            score -= deduction
        
        # Assurer que le score reste entre 0 et 100
        return max(0, min(100, score))
    
    def _update_summary(self, risks: List[Dict]) -> Dict:
        """
        Met à jour le résumé des risques
        
        Args:
            risks: Liste des risques
            
        Returns:
            Résumé par catégorie de sévérité
        """
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total": len(risks)
        }
        
        for risk in risks:
            severity = risk.get('severity', '').lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def _generate_recommendations(self, risks: List[Dict]) -> List[str]:
        """
        Génère des recommandations basées sur les risques
        
        Args:
            risks: Liste des risques
            
        Returns:
            Liste des recommandations
        """
        recommendations = []
        seen_recommendations = set()
        
        for risk in risks:
            rec = risk.get('recommendation', '')
            if rec and rec not in seen_recommendations:
                recommendations.append({
                    'priority': risk.get('severity', 'MEDIUM'),
                    'action': rec
                })
                seen_recommendations.add(rec)
        
        # Trier par priorité
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations
    
    def _llm_deep_analysis(self, config_data: Dict, risks: List[Dict]) -> Dict:
        """
        Utilise le LLM pour une analyse approfondie
        
        Args:
            config_data: Données de configuration
            risks: Risques déjà identifiés
            
        Returns:
            Analyse LLM
        """
        if not self.llm:
            return {"error": "LLM non disponible"}
        
        try:
            # Préparer le contexte pour le LLM
            context = {
                'risks_found': risks[:10],  # Limiter pour ne pas dépasser le contexte
                'config_summary': {
                    'user_count': len(config_data.get('users', [])),
                    'role_count': len(config_data.get('roles', [])),
                    'privilege_count': len(config_data.get('system_privileges', []))
                }
            }
            
            # Générer des exemples pour few-shot learning
            examples = self.generate_security_examples()
            
            # Créer le prompt
            prompt = f"""
            Analyse de sécurité Oracle - Rapport d'audit
            
            Résumé des risques identifiés: {len(risks)} risques
            
            Configuration:
            - Utilisateurs: {context['config_summary']['user_count']}
            - Rôles: {context['config_summary']['role_count']}
            - Privilèges: {context['config_summary']['privilege_count']}
            
            Exemples de risques typiques:
            {json.dumps(examples[:3], indent=2)}
            
            Risques identifiés (premiers 10):
            {json.dumps(risks[:10], indent=2)}
            
            Analyse approfondie demandée:
            1. Y a-t-il des risques non détectés par les règles automatiques?
            2. Quelles sont les vulnérabilités potentielles les plus critiques?
            3. Recommandations stratégiques à long terme.
            
            Format de réponse JSON:
            {{
                "unseen_risks": [],
                "critical_vulnerabilities": [],
                "strategic_recommendations": []
            }}
            """
            
            # Appeler le LLM
            response = self.llm.generate(prompt)
            
            # Essayer de parser la réponse JSON
            try:
                return json.loads(response)
            except:
                return {"raw_response": response}
                
        except Exception as e:
            return {"error": f"Erreur LLM: {str(e)}"}
    
    def generate_report(self, report_data: Dict, format: str = 'json') -> str:
        """
        Génère le rapport d'audit
        
        Args:
            report_data: Données du rapport
            format: Format de sortie ('json', 'html', 'md')
            
        Returns:
            Chemin du fichier généré ou contenu
        """
        os.makedirs('data/reports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            filename = f'data/reports/security_audit_{timestamp}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Rapport JSON généré: {filename}")
            return filename
        
        elif format == 'html':
            filename = f'data/reports/security_audit_{timestamp}.html'
            html_content = self._generate_html_report(report_data)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Rapport HTML généré: {filename}")
            return filename
        
        elif format == 'md':
            filename = f'data/reports/security_audit_{timestamp}.md'
            md_content = self._generate_markdown_report(report_data)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"✅ Rapport Markdown généré: {filename}")
            return filename
        
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """
        Génère un rapport HTML
        
        Args:
            report_data: Données du rapport
            
        Returns:
            Contenu HTML
        """
        # Échapper les caractères spéciaux
        def escape_html(text):
            if isinstance(text, str):
                return html.escape(text)
            return str(text)
        
        # Générer le HTML
        html_template = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport d'Audit de Sécurité Oracle</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }}
                .score {{ font-size: 48px; font-weight: bold; margin: 20px 0; }}
                .score-good {{ color: #27ae60; }}
                .score-medium {{ color: #f39c12; }}
                .score-poor {{ color: #e74c3c; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
                .summary-item {{ padding: 15px; border-radius: 5px; text-align: center; }}
                .critical {{ background-color: #ffebee; border: 1px solid #ef9a9a; }}
                .high {{ background-color: #fff3e0; border: 1px solid #ffcc80; }}
                .medium {{ background-color: #fff8e1; border: 1px solid #fff59d; }}
                .low {{ background-color: #e8f5e9; border: 1px solid #a5d6a7; }}
                .risk-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .risk-table th, .risk-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                .risk-table th {{ background-color: #3498db; color: white; }}
                .severity-critical {{ color: #c62828; font-weight: bold; }}
                .severity-high {{ color: #ef6c00; font-weight: bold; }}
                .severity-medium {{ color: #f9a825; font-weight: bold; }}
                .severity-low {{ color: #2e7d32; font-weight: bold; }}
                .recommendations {{ background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .recommendation-item {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #2196f3; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Rapport d'Audit de Sécurité Oracle</h1>
                    <p>Généré le {escape_html(report_data.get('timestamp', ''))}</p>
                    
                    <div class="score {self._get_score_class(report_data.get('score', 0))}">
                        {report_data.get('score', 0)}/100
                    </div>
                </div>
                
                <div class="summary">
                    <div class="summary-item critical">
                        <h3>⚠️ Critique</h3>
                        <p>{report_data.get('summary', {}).get('critical', 0)}</p>
                    </div>
                    <div class="summary-item high">
                        <h3>🔴 Haute</h3>
                        <p>{report_data.get('summary', {}).get('high', 0)}</p>
                    </div>
                    <div class="summary-item medium">
                        <h3>🟡 Moyenne</h3>
                        <p>{report_data.get('summary', {}).get('medium', 0)}</p>
                    </div>
                    <div class="summary-item low">
                        <h3>🟢 Basse</h3>
                        <p>{report_data.get('summary', {}).get('low', 0)}</p>
                    </div>
                </div>
                
                <h2>📋 Résumé des Risques ({report_data.get('summary', {}).get('total', 0)})</h2>
                <table class="risk-table">
                    <thead>
                        <tr>
                            <th>Sévérité</th>
                            <th>Type</th>
                            <th>Description</th>
                            <th>Détails</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_risk_rows(report_data.get('risks', []))}
                    </tbody>
                </table>
                
                <h2>✅ Recommandations ({len(report_data.get('recommendations', []))})</h2>
                <div class="recommendations">
                    {self._generate_recommendation_items(report_data.get('recommendations', []))}
                </div>
                
                {self._generate_llm_section(report_data.get('llm_analysis', {}))}
                
                <div class="footer">
                    <p>Rapport généré automatiquement par Oracle AI Security Platform</p>
                    <p>⚠️ Ce rapport est à des fins informatives uniquement. Consultez un expert en sécurité pour validation.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_risk_rows(self, risks: List[Dict]) -> str:
        """Génère les lignes du tableau de risques pour HTML"""
        rows = []
        for risk in risks[:50]:  # Limiter à 50 risques pour la lisibilité
            severity_class = f"severity-{risk.get('severity', '').lower()}"
            row = f"""
            <tr>
                <td><span class="{severity_class}">{risk.get('severity', '')}</span></td>
                <td>{html.escape(str(risk.get('type', '')))}</td>
                <td>{html.escape(str(risk.get('description', '')))}</td>
                <td>{html.escape(str(risk.get('details', '')))}</td>
            </tr>
            """
            rows.append(row)
        
        if not rows:
            return "<tr><td colspan='4'>Aucun risque identifié</td></tr>"
        
        return "\n".join(rows)
    
    def _generate_recommendation_items(self, recommendations: List[Dict]) -> str:
        """Génère les éléments de recommandation pour HTML"""
        items = []
        for i, rec in enumerate(recommendations, 1):
            item = f"""
            <div class="recommendation-item">
                <strong>#{i} [{rec.get('priority', '')}]</strong><br>
                {html.escape(str(rec.get('action', '')))}
            </div>
            """
            items.append(item)
        
        if not items:
            return "<p>Aucune recommandation</p>"
        
        return "\n".join(items)
    
    def _generate_llm_section(self, llm_analysis: Dict) -> str:
        """Génère la section d'analyse LLM pour HTML"""
        if not llm_analysis or 'error' in llm_analysis:
            return ""
        
        analysis_html = "<h2>🤖 Analyse IA Avancée</h2>"
        
        if 'unseen_risks' in llm_analysis and llm_analysis['unseen_risks']:
            analysis_html += "<h3>Risques potentiels non détectés:</h3><ul>"
            for risk in llm_analysis['unseen_risks']:
                analysis_html += f"<li>{html.escape(str(risk))}</li>"
            analysis_html += "</ul>"
        
        if 'strategic_recommendations' in llm_analysis and llm_analysis['strategic_recommendations']:
            analysis_html += "<h3>Recommandations stratégiques:</h3><ul>"
            for rec in llm_analysis['strategic_recommendations']:
                analysis_html += f"<li>{html.escape(str(rec))}</li>"
            analysis_html += "</ul>"
        
        return f'<div class="llm-analysis">{analysis_html}</div>'
    
    def _get_score_class(self, score: int) -> str:
        """Détermine la classe CSS basée sur le score"""
        if score >= 80:
            return "score-good"
        elif score >= 60:
            return "score-medium"
        else:
            return "score-poor"
    
    def _generate_markdown_report(self, report_data: Dict) -> str:
        """
        Génère un rapport en format Markdown
        
        Args:
            report_data: Données du rapport
            
        Returns:
            Contenu Markdown
        """
        md = f"""# 🔒 Rapport d'Audit de Sécurité Oracle

**Date**: {report_data.get('timestamp', '')}

## 📊 Score de Sécurité

# **{report_data.get('score', 0)}/100** {self._get_score_emoji(report_data.get('score', 0))}

## 📈 Résumé des Risques

| Sévérité | Nombre |
|----------|--------|
| ⚠️ Critique | {report_data.get('summary', {}).get('critical', 0)} |
| 🔴 Haute | {report_data.get('summary', {}).get('high', 0)} |
| 🟡 Moyenne | {report_data.get('summary', {}).get('medium', 0)} |
| 🟢 Basse | {report_data.get('summary', {}).get('low', 0)} |
| **Total** | **{report_data.get('summary', {}).get('total', 0)}** |

## 📋 Risques Détectés

"""
        
        # Ajouter les risques
        for i, risk in enumerate(report_data.get('risks', [])[:20], 1):
            md += f"""### {i}. {risk.get('type', '')} - {risk.get('severity', '')}

**Description**: {risk.get('description', '')}

**Détails**: {risk.get('details', '')}

**Recommandation**: {risk.get('recommendation', '')}

---
"""
        
        # Ajouter les recommandations
        md += "\n## ✅ Recommandations\n\n"
        for i, rec in enumerate(report_data.get('recommendations', []), 1):
            md += f"{i}. **[{rec.get('priority', '')}]** {rec.get('action', '')}\n"
        
        # Ajouter l'analyse LLM si disponible
        if 'llm_analysis' in report_data and report_data['llm_analysis']:
            md += "\n## 🤖 Analyse IA Avancée\n\n"
            
            if 'unseen_risks' in report_data['llm_analysis']:
                md += "### Risques potentiels non détectés:\n"
                for risk in report_data['llm_analysis']['unseen_risks']:
                    md += f"- {risk}\n"
            
            if 'strategic_recommendations' in report_data['llm_analysis']:
                md += "\n### Recommandations stratégiques:\n"
                for rec in report_data['llm_analysis']['strategic_recommendations']:
                    md += f"- {rec}\n"
        
        md += f"""
---
*Rapport généré automatiquement par Oracle AI Security Platform*
*⚠️ Ce rapport est à des fins informatives uniquement. Consultez un expert en sécurité pour validation.*
"""
        
        return md
    
    def _get_score_emoji(self, score: int) -> str:
        """Retourne l'emoji approprié pour le score"""
        if score >= 80:
            return "✅"
        elif score >= 60:
            return "⚠️"
        else:
            return "❌"

    def generate_sample_report(self) -> Dict:
        """
        Génère un rapport d'audit de démonstration pour les tests
        
        Returns:
            Rapport d'audit de démonstration
        """
        from datetime import datetime
        
        return {
            "timestamp": datetime.now().isoformat(),
            "score": 85,
            "risks": [
                {
                    "type": "WEAK_PASSWORD",
                    "severity": "HIGH",
                    "description": "Mots de passe par défaut détectés sur 3 comptes",
                    "details": "Comptes: TEST_USER, GUEST, DEMO",
                    "recommendation": "Forcer le changement de mot de passe"
                },
                {
                    "type": "EXCESSIVE_PRIVILEGES",
                    "severity": "CRITICAL",
                    "description": "Privilège DBA accordé à un utilisateur non-admin",
                    "details": "Utilisateur: APP_USER a DBA",
                    "recommendation": "Révoquer DBA, donner des privilèges spécifiques"
                },
                {
                    "type": "AUDIT_DISABLED",
                    "severity": "MEDIUM",
                    "description": "Audit désactivé sur plusieurs schémas",
                    "details": "Schemas: HR, FINANCE",
                    "recommendation": "Activer l'audit minimal"
                }
            ],
            "recommendations": [
                {"priority": "CRITICAL", "action": "Révoquer les privilèges DBA inutiles"},
                {"priority": "HIGH", "action": "Changer tous les mots de passe par défaut"},
                {"priority": "MEDIUM", "action": "Activer l'audit sur tous les schémas critiques"}
            ],
            "summary": {
                "critical": 1,
                "high": 1,
                "medium": 1,
                "low": 0,
                "total": 3
            }
        }


# Fonction utilitaire pour tester
def test_security_audit():
    """Teste le module d'audit de sécurité"""
    print("=== Test du module SecurityAuditor ===")
    
    # Créer des données de test
    test_config = {
        'users': pd.DataFrame({
            'USERNAME': ['ADMIN', 'APP_USER', 'TEST', 'SYS', 'SYSTEM'],
            'ACCOUNT_STATUS': ['OPEN', 'OPEN', 'EXPIRED', 'OPEN', 'OPEN'],
            'PROFILE': ['DEFAULT', 'APP_PROFILE', 'DEFAULT', 'DEFAULT', 'DEFAULT']
        }),
        'roles': pd.DataFrame({
            'ROLE': ['DBA', 'APP_ROLE', 'PUBLIC'],
            'PASSWORD_REQUIRED': ['YES', 'NO', 'NO']
        }),
        'system_privileges': pd.DataFrame({
            'GRANTEE': ['ADMIN', 'PUBLIC', 'APP_USER'],
            'PRIVILEGE': ['DBA', 'CREATE SESSION', 'SELECT ANY TABLE']
        }),
        'profiles': pd.DataFrame({
            'PROFILE': ['DEFAULT', 'APP_PROFILE'],
            'RESOURCE_NAME': ['FAILED_LOGIN_ATTEMPTS', 'PASSWORD_REUSE_MAX'],
            'LIMIT': ['UNLIMITED', 'UNLIMITED']
        })
    }
    
    # Créer l'auditeur
    auditor = SecurityAuditor()
    
    # Générer des exemples
    examples = auditor.generate_security_examples()
    print(f"✅ {len(examples)} exemples de sécurité générés")
    
    # Exécuter l'audit
    report = auditor.audit_database(test_config)
    
    print(f"\nScore de sécurité: {report['score']}/100")
    print(f"Risques détectés: {report['summary']['total']}")
    print(f"  - Critique: {report['summary']['critical']}")
    print(f"  - Haute: {report['summary']['high']}")
    print(f"  - Moyenne: {report['summary']['medium']}")
    print(f"  - Basse: {report['summary']['low']}")
    
    # Générer un rapport
    report_file = auditor.generate_report(report, 'json')
    print(f"\n✅ Rapport généré: {report_file}")
    
    return report


if __name__ == "__main__":
    # Exécuter le test
    test_report = test_security_audit()
    print("\n=== Test terminé avec succès ===")