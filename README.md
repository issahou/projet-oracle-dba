# Oracle AI Platform – Setup & Usage


Plateforme intelligente de gestion de bases de données Oracle intégrant
**IA (LLM), RAG et automatisation DBA**.

Ce document explique **comment installer, configurer et utiliser l’application**.

---

## 1. Prérequis

### Logiciels requis
- Python **3.9+**
- Oracle Database (instance réelle ou simulée)
- Git
- (Optionnel) Docker

### Accès Oracle
- Instance Oracle locale ou distante
- Utilisateur avec droits de lecture sur :
  - `V$SQLSTAT`, `V$SQL_PLAN`
  - `AUD$`
  - `DBA_USERS`, `DBA_ROLES`, `DBA_SYS_PRIVS`

---

## 2. Installation du Projet

### a.  Cloner le dépôt

```bash
git clone https://github.com/issahou/projet-oracle-dba.git
cd oracle-ai-platform

```
### b. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate     # Linux / Mac
venv\Scripts\activate        # Windows
```
### c. Installer les dépendances
```bash
pip install -r requirements.txt
```
## 2. Configuration IA
Choix du LLM

Le projet supporte plusieurs modèles :

| LLM             | Mode  | Coût    |
| --------------- | ----- | ------- |
| Ollama (Llama2) | Local | Gratuit |
| OpenAI GPT-3.5  | API   | $5–15   |
| Claude API      | API   | ~$5     |

Comme LLM Ollama est lourd, on a adopté  Phi car :

- Léger → déploiement local
- Rapide → réponses quasi instantanées
- Très bon en raisonnement logique et technique
- Compatible avec RAG
- Pas besoin de cloud externe (important pour Oracle)

**Exemple configuration .env :**

```bash
ORACLE_USER=system
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/XE
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=phi:latest
```

## 3. Initialisation de la Base RAG
### 3.1. Charger les documents Oracle

```bash
python src/rag_setup.py
```

Cette étape :

- vectorise 15–20 documents Oracle

- initialise la base ChromaDB

- rend la base prête pour la recherche sémantique

### 3.2. Vérification
```bash
python tests/test_rag.py
```

Résultat attendu :

- récupération correcte du contexte Oracle

- réponses pertinentes du LLM

#### Lancer l’Application :

Démarrage du Dashboard
```bash
python src/dashboard_phi.py
```
Par défaut :

http://localhost:8501

Mais comme l’Application est déjà deployée, vous pouvez accéder directement dans ce lien pour tester : 

https://stethoscopic-revivably-jamey.ngrok-free.dev

## 4. Tests
### Lancer tous les tests :

```bash
pytest tests/
```
Critères validés :

- modules fonctionnels

- réponses IA cohérentes

- intégration RAG + LLM

- stabilité du dashboard

**Les résultats détaillés sont disponibles dans RESULTS.md.**

## 5. Structure du Projet
```bash
PROJET-ORACLE-DBA/
│
├── images/
│   └── (Diagrams, screenshots, architecture visuals)
│
├── oracle-ai-platform/
│   │
│   ├── __pycache__/
│   │   └── config.cpython-39.pyc
│   │
│   ├── data/
│   │   ├── chroma_db/        # Vector database (RAG embeddings)
│   │   ├── extracted/        # Extracted Oracle data & logs
│   │   └── prompts.yaml     # Prompt templates for LLM interactions
│   │
│   ├── docs/
│   │   └── oracle/
│   │       └── best_practices.txt   # Oracle DBA best practices
│   │
│   ├── src/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   │
│   │   ├── anomaly_detector.py      # Detects performance anomalies
│   │   ├── backup_recommender.py    # Backup strategy recommendations
│   │   ├── dashboard_phi.py         # Web dashboard & chatbot logic
│   │   ├── data_extractor.py        # Oracle data extraction (V$ views, logs)
│   │   ├── llm_engine_phi.py        # LLM Phi integration layer
│   │   ├── query_optimizer.py       # SQL tuning & execution plan analysis
│   │   ├── rag_engine.py            # Core RAG logic
│   │   ├── rag_integration.py       # RAG + LLM orchestration
│   │   ├── rag_setup.py             # Vector DB initialization & indexing
│   │   ├── recovery_guide.py        # Disaster recovery recommendations
│   │   └── security_audit.py        # Oracle security & audit analysis
│   │
│   ├── tests/
│   │   └── (Unit and integration tests)
│   │
│   ├── .env                         # Environment variables
│   ├── app_run.py                   # Application entry point
│   └── requirements.txt             # Python dependencies
│
├── ARCHITECTURE.md                  # System architecture description
├── RESULTS.md                       # Test results and evaluation
└── README.md                        # Project documentation

```

## 6. Contexte Académique

Ce projet a été réalisé dans un cadre pédagogique visant à :

- maîtriser le Prompt Engineering

- comprendre l’architecture RAG

- appliquer l’administration Oracle avancée

- développer une application fullstack avec IA


## 7. Conclusion

Cette plateforme démontre comment l’IA peut :

- assister un administrateur Oracle,

- prévenir les incidents,

- améliorer la sécurité et la performance,

- tout en restant explicable et maîtrisable.

**Un expert Oracle virtuel, disponible 24/7.**

### Réalisé par :

- **OUEDRAOGO Youssahou**

- **RAHELIARISOA Andriamasy Lorraine Agnès** 
 
 Deuxième année – Cycle Ingénieur  
 Filière : **LSI (Logiciels et Systèmes Intelligents)**  à la  Faculté des Sciences et Techniques de Tanger

### Encadré par :
 **Professeur Mohamed BEN AHMED**
 
**Module Administration de la base de données Oracle**
