# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration Oracle
    ORACLE_USER = os.getenv("ORACLE_USER", "system")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "password")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost:1521/XE")
    
    # Configuration LLM
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama2")
    
    # Chemins
    DATA_DIR = "data"
    REPORTS_DIR = "data/reports"
    EXTRACTED_DIR = "data/extracted"
    
    @classmethod
    def create_directories(cls):
        """Crée les répertoires nécessaires"""
        for directory in [cls.DATA_DIR, cls.REPORTS_DIR, cls.EXTRACTED_DIR]:
            os.makedirs(directory, exist_ok=True)

Config.create_directories()