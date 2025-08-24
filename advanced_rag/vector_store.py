"""
Vector Store Management - Step 2: Get vector storage working
"""
import os
import sys
sys.path.append('..')

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
import requests
from config_advanced import *

class VectorStoreManager:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = None
        self.collection = None
        self.setup_vector_store()
    
    def setup_vector_store(self):
        """Initialize ChromaDB vector store"""
        print("🔧 Setting up ChromaDB vector store...")
        
        # Create vector store directory
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("survey_responses")
            print(f"✅ Loaded existing collection with {self.collection.count()} documents")
        except:
            self.collection = self.client.create_collection(
                name="survey_responses",
                metadata={"description": "Survey responses with embeddings"}
            )
            print("✅ Created new collection")
    
    def fetch_survey_data(self) -> List[Dict]:
        """Fetch survey data from snapshot or Supabase"""
        # Try to load from snapshot first
        snapshot_file = "data_snapshot.json"
        if os.path.exists(snapshot_file):
            print(f"📥 Loading survey data from snapshot: {snapshot_file}")
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            responses = data.get('responses', [])
            print(f"✅ Loaded {len(responses)} survey responses from snapshot")
            return responses
        
        # Fallback to direct Supabase fetch
        print("📥 Fetching survey data from Supabase...")
        
        url = f"{SUPABASE_URL}/rest/v1/responses"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {"select": "*"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Fetched {len(data)} survey responses")
            return data
        else:
            print(f"❌ Failed to fetch data: {response.status_code}")
            return []
    
    def prepare_documents(self, survey_data: List[Dict]) -> List[Dict]:
        """Prepare documents for vector storage"""
        print("📝 Preparing documents for embedding...")
        
        documents = []
        
        for item in survey_data:
            # Skip empty responses
            response_value = item.get('response_value', '').strip()
            if not response_value:
                continue
            
            # Handle different response types
            question_info = item.get('questions', {}) or {}
            question_type = question_info.get('question_type', '')
            
            # For MCQ responses, expand the single letter to full text
            if question_type == 'mcq' and len(response_value) == 1:
                mcq_options = question_info.get('mcq_options', {})
                full_response = mcq_options.get(response_value, response_value)
                response_text = f"Selected: {full_response}"
            else:
                response_text = response_value
            
            # Skip very short responses that aren't MCQ
            if len(response_text) < 10 and question_type != 'mcq':
                continue
            
            # Create document
            question_info = item.get('questions', {}) or {}
            
            doc = {
                'id': str(item.get('response_id', item.get('id', 'unknown'))),
                'text': response_text,
                'metadata': {
                    'charity_name': item.get('charity_name', ''),
                    'age_group': item.get('age_group', ''),
                    'gender': item.get('gender', ''),
                    'question_text': question_info.get('question_text', ''),
                    'question_type': question_info.get('question_type', ''),
                    'response_length': len(response_text),
                    'original_response': response_value
                }
            }
            
            documents.append(doc)
        
        print(f"✅ Prepared {len(documents)} documents for embedding")
        return documents
    
    def add_documents_to_vector_store(self, documents: List[Dict]):
        """Add documents to vector store with embeddings"""
        print("🔄 Adding documents to vector store...")
        
        if not documents:
            print("❌ No documents to add")
            return
        
        # Prepare data for ChromaDB
        ids = [doc['id'] for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        # Generate embeddings
        print("🧠 Generating embeddings...")
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"✅ Added {len(documents)} documents to vector store")
        print(f"Total documents in collection: {self.collection.count()}")
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents"""
        print(f"🔍 Searching for: '{query}'")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search in vector store
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        print(f"✅ Found {len(formatted_results)} similar documents")
        return formatted_results
    
    def test_vector_search(self):
        """Test vector search functionality"""
        print("\n🧪 Testing Vector Search")
        print("-" * 40)
        
        test_queries = [
            "building confidence and self-esteem",
            "making friends and social connections",
            "creative activities and filmmaking",
            "leadership and taking initiative",
            "overcoming challenges and resilience"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = self.search_similar(query, n_results=3)
            
            for i, result in enumerate(results):
                print(f"  {i+1}. Score: {result['similarity_score']:.3f}")
                print(f"     Text: {result['text'][:100]}...")
                print(f"     Org: {result['metadata'].get('charity_name', 'Unknown')}")
    
    def populate_vector_store(self):
        """Full pipeline to populate vector store"""
        print("🚀 POPULATING VECTOR STORE")
        print("=" * 50)
        
        # Check if already populated
        if self.collection.count() > 0:
            print(f"Collection already has {self.collection.count()} documents")
            choice = input("Repopulate? (y/n): ").lower()
            if choice != 'y':
                return
            
            # Clear existing data
            self.client.delete_collection("survey_responses")
            self.collection = self.client.create_collection("survey_responses")
        
        # Fetch and process data
        survey_data = self.fetch_survey_data()
        if not survey_data:
            return
        
        documents = self.prepare_documents(survey_data)
        self.add_documents_to_vector_store(documents)
        
        # Test the populated store
        self.test_vector_search()
        
        print("\n✅ Vector store population complete!")

if __name__ == "__main__":
    manager = VectorStoreManager()
    manager.populate_vector_store()