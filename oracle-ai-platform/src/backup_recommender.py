# src/backup_recommender.py
from enum import Enum
from dataclasses import dataclass

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

@dataclass
class BackupStrategy:
    type: BackupType
    frequency: str
    retention_days: int
    storage_location: str
    estimated_cost: float

class BackupRecommender:
    def __init__(self, llm_engine):
        self.llm = llm_engine
        
    def recommend_strategy(self, requirements: Dict) -> BackupStrategy:
        """Recommande une stratégie de sauvegarde"""
        prompt_vars = {
            "rpo": requirements.get('rpo', '24h'),
            "rto": requirements.get('rto', '4h'),
            "data_size": requirements.get('data_size', '100GB'),
            "budget": requirements.get('budget', 1000)
        }
        
        recommendation = self.llm.generate(
            "backup_recommendation",
            variables=prompt_vars
        )
        
        return self._parse_recommendation(recommendation)
    
    def generate_rman_script(self, strategy: BackupStrategy) -> str:
        """Génère un script RMAN basé sur la stratégie"""
        template = self._load_template(strategy.type)
        
        script = template.format(
            frequency=strategy.frequency,
            retention=strategy.retention_days,
            location=strategy.storage_location
        )
        
        return script