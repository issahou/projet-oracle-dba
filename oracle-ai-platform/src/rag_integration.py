# src/rag_integration.py - Intégration RAG avec Dashboard et LLM

from rag_engine import OracleRAGEngine
from llm_engine_phi import LLMEnginePhi
from typing import List, Dict, Optional

class RAGIntegration:
    """
    Classe d'intégration entre RAG (ChromaDB), LLM (Phi) et Dashboard
    """
    
    def __init__(self, llm_engine: Optional[LLMEnginePhi] = None):
        """
        Initialise l'intégration RAG
        
        Args:
            llm_engine: Instance du moteur LLM (optionnel)
        """
        print("🔧 Initialisation RAG Integration...")
        
        # Initialiser le moteur RAG
        self.rag_engine = OracleRAGEngine()
        self.llm_engine = llm_engine
        
        print("✅ RAG Integration prête")
    
    def retrieve_context(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Récupère le contexte pertinent depuis ChromaDB
        
        Args:
            query: Question ou requête utilisateur
            n_results: Nombre de documents à retourner (défaut: 5)
            
        Returns:
            Liste de documents pertinents avec métadonnées
        """
        try:
            # Recherche dans ChromaDB
            results = self.rag_engine.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Formater les résultats
            documents = []
            for i in range(len(results['documents'][0])):
                documents.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            print(f"📚 {len(documents)} documents récupérés pour: '{query[:50]}...'")
            return documents
            
        except Exception as e:
            print(f"❌ Erreur retrieve_context: {e}")
            return []
    
    def enhanced_llm_query(self, user_query: str, category: Optional[str] = None) -> str:
        """
        Requête LLM enrichie avec contexte RAG
        
        Args:
            user_query: Question utilisateur
            category: Catégorie pour filtrer le contexte (security, performance, backup, etc.)
            
        Returns:
            Réponse du LLM enrichie du contexte Oracle
        """
        if not self.llm_engine:
            return "⚠️ LLM Engine non disponible"
        
        try:
            # 1. Récupérer le contexte pertinent
            context_docs = self.retrieve_context(user_query, n_results=3)
            
            # 2. Construire le contexte enrichi
            context_text = "\n\n=== CONTEXTE ORACLE (Base de connaissances) ===\n"
            for i, doc in enumerate(context_docs, 1):
                context_text += f"\n--- Document {i} ({doc['metadata']['topic']}) ---\n"
                context_text += doc['content'][:1000]  # Limiter pour ne pas dépasser le contexte
                context_text += "\n"
            
            # 3. Construire le prompt enrichi
            enriched_prompt = f"""Tu es un expert Oracle DBA avec accès à une base de connaissances complète.

{context_text}

=== QUESTION DE L'UTILISATEUR ===
{user_query}

=== INSTRUCTIONS ===
Réponds à la question en t'appuyant sur le contexte Oracle ci-dessus.
Fournis des exemples SQL concrets et des commandes exécutables.
Si le contexte ne suffit pas, utilise tes connaissances générales Oracle.
"""
            
            # 4. Appeler le LLM avec le contexte enrichi
            response = self.llm_engine.generate(
                "chatbot_general",
                variables={
                    "query": enriched_prompt,
                    "history": ""
                },
                max_tokens=1200
            )
            
            return response
            
        except Exception as e:
            return f"❌ Erreur enhanced_llm_query: {str(e)}"
    
    def search_by_category(self, category: str, query: str = "", n_results: int = 10) -> List[Dict]:
        """
        Recherche dans une catégorie spécifique
        
        Args:
            category: Catégorie (security, performance, backup, monitoring, etc.)
            query: Terme de recherche (optionnel)
            n_results: Nombre de résultats
            
        Returns:
            Documents de la catégorie
        """
        try:
            # Recherche avec filtre de catégorie
            results = self.rag_engine.collection.query(
                query_texts=[query if query else category],
                n_results=n_results,
                where={"category": category}
            )
            
            documents = []
            for i in range(len(results['documents'][0])):
                documents.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            return documents
            
        except Exception as e:
            print(f"❌ Erreur search_by_category: {e}")
            return []
    
    def get_related_documents(self, topic: str, n_results: int = 5) -> List[Dict]:
        """
        Obtient des documents reliés à un sujet
        
        Args:
            topic: Sujet (password_policy, index_strategy, etc.)
            n_results: Nombre de résultats
            
        Returns:
            Documents reliés
        """
        return self.retrieve_context(topic, n_results)
    
    def analyze_with_context(self, analysis_type: str, data: Dict) -> Dict:
        """
        Analyse enrichie avec contexte RAG
        
        Args:
            analysis_type: Type d'analyse (security, performance, backup)
            data: Données à analyser
            
        Returns:
            Résultat d'analyse avec recommandations contextuelles
        """
        try:
            # Récupérer contexte pertinent
            query = f"{analysis_type} analysis best practices"
            context_docs = self.retrieve_context(query, n_results=3)
            
            # Construire le contexte pour LLM
            context_summary = "\n".join([
                f"- {doc['metadata']['topic']}: {doc['content'][:200]}..."
                for doc in context_docs
            ])
            
            if not self.llm_engine:
                return {
                    "analysis": "LLM non disponible",
                    "context_used": context_summary,
                    "recommendations": ["Activer le LLM pour analyse complète"]
                }
            
            # Analyser avec LLM + contexte
            if analysis_type == "security":
                result = self.llm_engine.assess_security(data)
                result['context_applied'] = context_summary
                return result
                
            elif analysis_type == "performance":
                # Extraire requête SQL si présente
                sql_query = data.get('sql_text', '')
                result = self.llm_engine.analyze_query(sql_query, "")
                return {
                    "analysis": result,
                    "context_applied": context_summary
                }
                
            elif analysis_type == "backup":
                result = self.llm_engine.get_backup_strategy(data)
                result['context_applied'] = context_summary
                return result
            
            return {"error": f"Type d'analyse inconnu: {analysis_type}"}
            
        except Exception as e:
            return {"error": f"Erreur analyse: {str(e)}"}
    
    def add_custom_document(self, content: str, category: str, topic: str, 
                           metadata: Optional[Dict] = None) -> bool:
        """
        Ajoute un document personnalisé à la base de connaissances
        
        Args:
            content: Contenu du document
            category: Catégorie
            topic: Sujet
            metadata: Métadonnées supplémentaires
            
        Returns:
            True si ajouté avec succès
        """
        try:
            import uuid
            doc_id = f"custom_{uuid.uuid4().hex[:8]}"
            
            doc_metadata = {
                'category': category,
                'topic': topic,
                'source': 'custom',
                'severity': metadata.get('severity', 'INFO') if metadata else 'INFO'
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            self.rag_engine.collection.add(
                documents=[content],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            print(f"✅ Document ajouté: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur add_custom_document: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """
        Obtient les statistiques de la collection ChromaDB
        
        Returns:
            Statistiques (nombre de documents, catégories, etc.)
        """
        try:
            count = self.rag_engine.collection.count()
            
            # Récupérer quelques documents pour analyser les catégories
            sample = self.rag_engine.collection.get(limit=count)
            
            categories = {}
            topics = {}
            
            for metadata in sample['metadatas']:
                cat = metadata.get('category', 'unknown')
                topic = metadata.get('topic', 'unknown')
                
                categories[cat] = categories.get(cat, 0) + 1
                topics[topic] = topics.get(topic, 0) + 1
            
            return {
                'total_documents': count,
                'categories': categories,
                'topics': topics,
                'collection_name': self.rag_engine.collection.name
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def test_retrieval(self, test_queries: List[str] = None) -> Dict:
        """
        Teste le système de récupération avec requêtes prédéfinies
        
        Args:
            test_queries: Liste de requêtes de test (optionnel)
            
        Returns:
            Résultats des tests
        """
        if test_queries is None:
            test_queries = [
                "index lent",
                "sécurité mot de passe",
                "backup RMAN",
                "requête SELECT performance",
                "audit Oracle"
            ]
        
        results = {}
        
        for query in test_queries:
            docs = self.retrieve_context(query, n_results=3)
            results[query] = {
                'found': len(docs),
                'top_topics': [doc['metadata']['topic'] for doc in docs],
                'relevance': [doc.get('distance', 0) for doc in docs]
            }
        
        return results


# ========================================
# FONCTIONS UTILITAIRES POUR LE DASHBOARD
# ========================================

def initialize_rag_for_dashboard(llm_engine: Optional[LLMEnginePhi] = None) -> RAGIntegration:
    """
    Fonction d'initialisation pour le dashboard Streamlit
    
    Args:
        llm_engine: Instance du moteur LLM
        
    Returns:
        Instance RAGIntegration prête à l'emploi
    """
    print("🚀 Initialisation RAG pour Dashboard...")
    rag_integration = RAGIntegration(llm_engine)
    
    # Test de connexion
    stats = rag_integration.get_collection_stats()
    print(f"📊 Stats: {stats['total_documents']} documents dans {len(stats['categories'])} catégories")
    
    return rag_integration


def test_rag_integration():
    """
    Fonction de test complète de l'intégration RAG
    """
    print("\n" + "="*60)
    print("🧪 TEST COMPLET DE L'INTÉGRATION RAG")
    print("="*60 + "\n")
    
    # 1. Initialiser
    print("1️⃣ Initialisation...")
    rag = RAGIntegration()
    
    # 2. Statistiques
    print("\n2️⃣ Statistiques de la collection...")
    stats = rag.get_collection_stats()
    print(f"   Documents totaux: {stats['total_documents']}")
    print(f"   Catégories: {list(stats['categories'].keys())}")
    print(f"   Topics: {list(stats['topics'].keys())[:5]}...")
    
    # 3. Test de récupération
    print("\n3️⃣ Test de récupération...")
    test_results = rag.test_retrieval()
    for query, result in test_results.items():
        print(f"   Query: '{query}'")
        print(f"     → {result['found']} documents trouvés")
        print(f"     → Topics: {result['top_topics']}")
    
    # 4. Recherche par catégorie
    print("\n4️⃣ Recherche par catégorie...")
    security_docs = rag.search_by_category("security", "password")
    print(f"   Documents 'security': {len(security_docs)}")
    
    # 5. Documents reliés
    print("\n5️⃣ Documents reliés...")
    related = rag.get_related_documents("index_strategy")
    print(f"   Documents reliés à 'index_strategy': {len(related)}")
    
    # 6. Ajout document personnalisé (test)
    print("\n6️⃣ Ajout document personnalisé...")
    success = rag.add_custom_document(
        content="Exemple de document custom pour test",
        category="test",
        topic="test_integration"
    )
    print(f"   Ajout: {'✅ Succès' if success else '❌ Échec'}")
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Exécuter les tests
    test_rag_integration()