# src/rag_setup.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import PyPDF2
import os

class RAGSetup:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./data/chroma_db"
        ))
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def load_oracle_documents(self, docs_directory):
        """Charge les documents Oracle pour le contexte"""
        documents = []
        metadatas = []
        ids = []
        
        # Parcourir les fichiers de documentation
        for filename in os.listdir(docs_directory):
            if filename.endswith('.pdf'):
                text = self._extract_pdf_text(
                    os.path.join(docs_directory, filename)
                )
            elif filename.endswith('.txt'):
                with open(os.path.join(docs_directory, filename), 'r') as f:
                    text = f.read()
            
            # Découper en chunks
            chunks = self._chunk_text(text, 500)
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": filename,
                    "chunk": i,
                    "doc_type": "oracle_best_practice"
                })
                ids.append(f"{filename}_{i}")
        
        return documents, metadatas, ids
    
    def create_collection(self, collection_name="oracle_docs"):
        """Crée une collection dans ChromaDB"""
        collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self._embed_function
        )
        
        # Charger les documents
        docs, metas, ids = self.load_oracle_documents("docs/oracle/")
        collection.add(
            documents=docs,
            metadatas=metas,
            ids=ids
        )
        
        return collection
    
    def retrieve_context(self, query, n_results=5):
        """Récupère les documents pertinents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0]