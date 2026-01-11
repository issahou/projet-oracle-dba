# src/recovery_guide.py
class RecoveryGuide:
    SCENARIOS = {
        "full_recovery": {
            "description": "Restauration complète après crash",
            "questions": [
                "Avez-vous les sauvegardes RMAN complètes ?",
                "Quand s'est produit le crash ?",
                "Où sont stockées les sauvegardes ?"
            ]
        },
        "pitr": {
            "description": "Récupération à un point dans le temps",
            "questions": [
                "Quelle date/heure cible ?",
                "Avez-vous les archives logs ?",
                "Jusqu'à quand pouvez-vous perdre des données ?"
            ]
        }
    }
    
    def guide_recovery(self, scenario: str, answers: Dict) -> str:
        """Guide l'utilisateur dans la récupération"""
        playbook = self.llm.generate(
            f"recovery_{scenario}",
            variables={"answers": json.dumps(answers)}
        )
        
        return self._format_playbook(playbook)
    
    def _format_playbook(self, playbook_text: str) -> Dict:
        """Formate le playbook en étapes structurées"""
        steps = playbook_text.split('\n\n')
        
        return {
            "scenario": self.current_scenario,
            "estimated_time": self._extract_time(steps),
            "prerequisites": self._extract_prerequisites(steps),
            "steps": [
                {
                    "number": i + 1,
                    "description": step,
                    "command": self._extract_command(step),
                    "validation": self._extract_validation(step)
                }
                for i, step in enumerate(steps)
            ]
        }