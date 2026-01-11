# src/query_optimizer.py
import re
from typing import List, Dict

class QueryOptimizer:
    def __init__(self, llm_engine):
        self.llm = llm_engine
        self.slow_queries = []
        
    def capture_slow_queries(self, threshold_ms=1000):
        """Capture les requêtes lentes"""
        # Implémentation de capture depuis V$SQLSTAT
        pass
    
    def analyze_query_performance(self, sql_id: str):
        """Analyse complète d'une requête"""
        query_data = self._get_query_details(sql_id)
        plan = self._get_execution_plan(sql_id)
        
        analysis = self.llm.analyze_query(
            query_data['sql_text'],
            plan
        )
        
        recommendations = self._extract_recommendations(analysis)
        
        return {
            "sql_id": sql_id,
            "original_query": query_data['sql_text'],
            "execution_stats": query_data['stats'],
            "analysis": analysis,
            "recommendations": recommendations,
            "optimized_query": self._generate_optimized_version(
                query_data['sql_text'], 
                recommendations
            )
        }
    
    def _generate_optimized_version(self, original_sql, recommendations):
        """Génère une version optimisée"""
        # Implémentation basée sur les recommandations
        optimized = original_sql
        
        for rec in recommendations:
            if "INDEX" in rec['type']:
                optimized = self._add_index_hint(optimized, rec)
            elif "REWRITE" in rec['type']:
                optimized = self._rewrite_query(optimized, rec)
        
        return optimized