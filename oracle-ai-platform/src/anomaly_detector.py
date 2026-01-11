# src/anomaly_detector.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self, llm_engine):
        self.llm = llm_engine
        self.model = IsolationForest(contamination=0.1)
        
    def generate_synthetic_logs(self):
        """Génère un dataset synthétique de logs"""
        normal_patterns = [
            "SELECT * FROM employees WHERE department = 'Sales'",
            "UPDATE customers SET last_contact = SYSDATE WHERE id = 123",
            "INSERT INTO orders (customer_id, amount) VALUES (456, 99.99)"
        ]
        
        anomalous_patterns = [
            "SELECT * FROM sys.user$ WHERE type# = 0",
            "GRANT DBA TO attacker_user",
            "DROP TABLE financial_data CASCADE CONSTRAINTS"
        ]
        
        return {
            "normal": self._generate_logs(normal_patterns, 50),
            "anomalous": self._generate_logs(anomalous_patterns, 20)
        }
    
    def detect_anomalies(self, log_entry):
        """Détecte les anomalies dans un log"""
        # Analyse statistique
        features = self._extract_features(log_entry)
        prediction = self.model.predict([features])
        
        # Analyse sémantique avec LLM
        llm_analysis = self.llm.generate(
            "anomaly_detection",
            variables={"log_entry": log_entry}
        )
        
        return {
            "log": log_entry,
            "statistical_score": float(prediction[0]),
            "llm_analysis": llm_analysis,
            "risk_level": self._determine_risk_level(
                prediction[0], llm_analysis
            )
        }