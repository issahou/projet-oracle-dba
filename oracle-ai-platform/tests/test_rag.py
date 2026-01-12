# test_rag.py - Test Simple du système RAG
import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_rag_engine():
    """Test du moteur RAG uniquement"""
    print("\n" + "="*60)
    print("🧪 TEST 1: RAG ENGINE (ChromaDB)")
    print("="*60)
    
    try:
        from rag_engine import OracleRAGEngine
        
        print("\n1️⃣ Initialisation...")
        rag = OracleRAGEngine()
        
        print(f"\n2️⃣ Vérification documents...")
        count = rag.collection.count()
        print(f"   📊 Documents: {count}")
        
        if count == 0:
            print("   ❌ ERREUR: Aucun document chargé!")
            return False
        
        print(f"\n3️⃣ Test recherche...")
        results = rag.collection.query(
            query_texts=["index lent"],
            n_results=3
        )
        
        print(f"   ✅ {len(results['documents'][0])} résultats trouvés")
        for i, doc in enumerate(results['documents'][0], 1):
            print(f"   {i}. {doc[:80]}...")
        
        print("\n✅ TEST RAG ENGINE: RÉUSSI")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST RAG ENGINE: ÉCHEC")
        print(f"   Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_integration():
    """Test de l'intégration RAG"""
    print("\n" + "="*60)
    print("🧪 TEST 2: RAG INTEGRATION")
    print("="*60)
    
    try:
        from rag_integration import RAGIntegration
        
        print("\n1️⃣ Initialisation...")
        rag_int = RAGIntegration(llm_engine=None)
        
        print(f"\n2️⃣ Stats collection...")
        stats = rag_int.get_collection_stats()
        print(f"   Documents: {stats['total_documents']}")
        print(f"   Catégories: {list(stats['categories'].keys())}")
        
        if stats['total_documents'] == 0:
            print("   ❌ ERREUR: Collection vide!")
            return False
        
        print(f"\n3️⃣ Test retrieve_context...")
        docs = rag_int.retrieve_context("optimisation requête", 3)
        print(f"   ✅ {len(docs)} documents récupérés")
        
        print(f"\n4️⃣ Test test_retrieval...")
        test_results = rag_int.test_retrieval()
        for query, result in list(test_results.items())[:2]:
            print(f"   '{query}': {result['found']} docs")
        
        print("\n✅ TEST RAG INTEGRATION: RÉUSSI")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST RAG INTEGRATION: ÉCHEC")
        print(f"   Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_import():
    """Test import dashboard"""
    print("\n" + "="*60)
    print("🧪 TEST 3: DASHBOARD IMPORT")
    print("="*60)
    
    try:
        print("\n1️⃣ Import dashboard_phi...")
        from dashboard_phi import OracleAIDashboardPhi
        
        print("   ✅ Import réussi")
        
        print("\n2️⃣ Vérification imports RAG dans dashboard...")
        import dashboard_phi
        
        # Vérifier que RAGIntegration est importé
        if hasattr(dashboard_phi, 'RAGIntegration'):
            print("   ✅ RAGIntegration disponible")
        else:
            print("   ⚠️ RAGIntegration non trouvé (peut être OK si import try/except)")
        
        print("\n✅ TEST DASHBOARD IMPORT: RÉUSSI")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST DASHBOARD IMPORT: ÉCHEC")
        print(f"   Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("🚀 TEST COMPLET SYSTÈME RAG - Oracle AI Platform")
    print("="*70)
    
    results = []
    
    # Test 1: RAG Engine
    results.append(("RAG Engine", test_rag_engine()))
    
    # Test 2: RAG Integration
    results.append(("RAG Integration", test_rag_integration()))
    
    # Test 3: Dashboard Import
    results.append(("Dashboard Import", test_dashboard_import()))
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    for name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"  {name}: {status}")
    
    all_success = all(r[1] for r in results)
    
    print("\n" + "="*70)
    if all_success:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("="*70)
        print("\nVous pouvez maintenant lancer le dashboard:")
        print("  streamlit run app_phi.py")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("="*70)
        print("\nÉtapes de dépannage:")
        print("1. Vérifiez que ChromaDB est installé: pip install chromadb")
        print("2. Vérifiez que sentence-transformers est installé: pip install sentence-transformers")
        print("3. Supprimez data/chroma_db/ et relancez")
        print("4. Vérifiez les erreurs ci-dessus")
    
    print("\n")


if __name__ == "__main__":
    main()