# init.py
import os
import sys
import shutil
from pathlib import Path

def setup_project():
    """Configure l'environnement du projet"""
    
    print("🔧 Configuration de la plateforme Oracle AI")
    
    # Créer les répertoires
    directories = [
        'data',
        'data/reports',
        'data/extracted',
        'data/chroma_db',
        'docs/oracle',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Créé: {directory}")
    
    # Créer le fichier .env s'il n'existe pas
    env_file = '.env'
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("""# Configuration Oracle
ORACLE_USER=system
ORACLE_PASSWORD=votre_mot_de_passe
ORACLE_DSN=localhost:1521/xe

# Configuration Ollama
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434

# Configuration de l'application
DEBUG=True
LOG_LEVEL=INFO
""")
        print(f"✅ Créé: {env_file}")
    
    # Télécharger la documentation Oracle (exemples)
    docs_dir = 'docs/oracle'
    if not any(os.listdir(docs_dir)):
        print("📥 Téléchargement de la documentation Oracle...")
        # Ici vous pourriez télécharger des PDFs d'exemple
        with open(os.path.join(docs_dir, 'best_practices.txt'), 'w') as f:
            f.write("""Meilleures pratiques Oracle:
            1. Utiliser des profils de mot de passe forts
            2. Activer l'audit sur les opérations sensibles
            3. Appliquer le principe du moindre privilège
            4. Sauvegarder régulièrement
            5. Monitorer les performances""")
    
    # Installer Ollama si nécessaire
    print("\n📦 Vérification d'Ollama...")
    try:
        import ollama
        print("✅ Ollama est installé")
    except ImportError:
        print("⚠️  Ollama n'est pas installé. Installation...")
        os.system("curl -fsSL https://ollama.com/install.sh | sh")
    
    # Vérifier si le modèle est téléchargé
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get('models', [])
        if not any(m['name'].startswith('llama2') for m in models):
            print("📥 Téléchargement du modèle Llama2...")
            os.system("ollama pull llama2")
    except:
        print("⚠️  Ollama n'est pas démarré. Démarrer avec: ollama serve")
    
    print("\n✅ Configuration terminée!")
    print("\nPour démarrer:")
    print("1. Modifiez .env avec vos credentials Oracle")
    print("2. Démarrer Ollama: ollama serve")
    print("3. Lancer l'application: streamlit run src/dashboard.py")

if __name__ == "__main__":
    setup_project()