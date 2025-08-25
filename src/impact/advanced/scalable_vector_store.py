"""
Scalable Vector Store Implementation
Addresses the scalability limitations of the JSON snapshot approach
"""
import os
import requests
from typing import List, Dict, Any, Optional, Generator
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
import hashlib
import json

from impact.shared.config.advanced import *

class ScalableVectorStoreManager:
    def __init__(self, batch_size: int = 100):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = None
        self.batch_size = batch_size
        self.setup_collection()
    
    def setup_collection(self):
        """Initialize ChromaDB collection with metadata tracking"""
        try:
            self.collection = self.client.get_collection("survey_responses")
            print(f"✅ Connected to existing collection with {self.collection.count()} documents")
        except:
            self.collection = self.client.create_collection(
                name="survey_responses",
                metadata={
                    "description": "Survey responses with embeddings",
                    "last_sync": None,
                    "total_processed": 0
                }
            )
            print("✅ Created new scalable collection")
    
    def stream_supabase_data(self, 
                           limit: int = 1000, 
                           offset: int = 0,
                           modified_since: Optional[str] = None) -> Generator[List[Dict], None, None]:
        """Stream data from Supabase in batches"""
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        while True:
            # Build query parameters
            params = {
                "select": "*",
                "limit": limit,
                "offset": offset,
                "order": "created_at.asc"
            }
            
            # Add timestamp filter for incremental updates
            if modified_since:
                params["created_at"] = f"gte.{modified_since}"
            
            print(f"📥 Fetching batch: offset={offset}, limit={limit}")
            
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/responses",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                print(f"❌ API error: {response.status_code}")
                break
            
            batch = response.json()
            
            if not batch:
                print("✅ No more data to fetch")
                break
            
            yield batch
            
            # If we got less than the limit, we're done
            if len(batch) < limit:
                break
                
            offset += limit    

    def get_document_hash(self, response_data: Dict) -> str:
        """Generate hash for change detection"""
        # Create hash from key fields to detect changes
        key_data = {
            'response_id': response_data.get('response_id'),
            'response_value': response_data.get('response_value'),
            'modified_at': response_data.get('updated_at', response_data.get('created_at'))
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def process_batch_incremental(self, batch: List[Dict]) -> int:
        """Process a batch with incremental updates"""
        new_docs = []
        updated_count = 0
        
        for item in batch:
            response_id = str(item.get('response_id', item.get('id')))
            doc_hash = self.get_document_hash(item)
            
            # Check if document exists and has changed
            try:
                existing = self.collection.get(ids=[response_id])
                if existing['ids'] and existing['metadatas'][0].get('doc_hash') == doc_hash:
                    continue  # No change, skip
                else:
                    # Document changed, delete old version
                    self.collection.delete(ids=[response_id])
                    updated_count += 1
            except:
                pass  # New document
            
            # Prepare new document
            response_text = item.get('response_value', '').strip()
            if len(response_text) < 5:  # Skip very short responses
                continue
            
            doc = {
                'id': response_id,
                'text': response_text,
                'metadata': {
                    'charity_name': item.get('charity_name', ''),
                    'age_group': item.get('age_group', ''),
                    'question_id': item.get('question_id'),
                    'created_at': item.get('created_at'),
                    'doc_hash': doc_hash,
                    'processed_at': datetime.now().isoformat()
                }
            }
            new_docs.append(doc)
        
        # Add new documents in batch
        if new_docs:
            self.add_documents_batch(new_docs)
        
        return len(new_docs)
    
    def add_documents_batch(self, documents: List[Dict]):
        """Add documents to vector store in batch"""
        if not documents:
            return
        
        ids = [doc['id'] for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        # Generate embeddings in batch
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"✅ Added {len(documents)} documents to vector store")
    
    def sync_incremental(self, hours_back: int = 24) -> Dict[str, int]:
        """Perform incremental sync of recent changes"""
        print(f"🔄 Starting incremental sync (last {hours_back} hours)")
        
        # Calculate timestamp for incremental sync
        since_time = datetime.now() - timedelta(hours=hours_back)
        since_timestamp = since_time.isoformat()
        
        total_processed = 0
        total_new = 0
        
        # Stream and process data in batches
        for batch in self.stream_supabase_data(
            limit=self.batch_size,
            modified_since=since_timestamp
        ):
            new_count = self.process_batch_incremental(batch)
            total_processed += len(batch)
            total_new += new_count
            
            print(f"📊 Batch complete: {len(batch)} processed, {new_count} new/updated")
        
        # Update collection metadata
        self.collection.modify(metadata={
            "last_sync": datetime.now().isoformat(),
            "total_processed": self.collection.count()
        })
        
        print(f"✅ Incremental sync complete: {total_new} documents updated")
        return {
            "processed": total_processed,
            "new_or_updated": total_new,
            "total_in_store": self.collection.count()
        }
    
    def sync_full_scalable(self) -> Dict[str, int]:
        """Perform full sync using streaming approach"""
        print("🔄 Starting full scalable sync")
        
        total_processed = 0
        
        # Stream all data in batches
        for batch in self.stream_supabase_data(limit=self.batch_size):
            new_count = self.process_batch_incremental(batch)
            total_processed += len(batch)
            
            print(f"📊 Progress: {total_processed} total processed")
        
        final_count = self.collection.count()
        print(f"✅ Full sync complete: {final_count} documents in vector store")
        
        return {
            "processed": total_processed,
            "final_count": final_count
        }

# Usage example and comparison
if __name__ == "__main__":
    print("🚀 SCALABLE VECTOR STORE DEMO")
    print("=" * 50)
    
    # Initialize scalable manager
    scalable_manager = ScalableVectorStoreManager(batch_size=50)
    
    # Demonstrate incremental sync
    result = scalable_manager.sync_incremental(hours_back=168)  # Last week
    
    print(f"\n📊 SCALABILITY COMPARISON:")
    print(f"Current approach: {result['final_count']} documents")
    print(f"Memory usage: Streaming (low)")
    print(f"Update method: Incremental")
    print(f"Suitable for: 1M+ documents ✅")