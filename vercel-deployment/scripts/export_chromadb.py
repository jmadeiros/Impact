#!/usr/bin/env python3
"""
ChromaDB Export Utility for Vercel Deployment Migration
Exports all documents and embeddings from existing ChromaDB collection
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Add parent directory to path to import from existing codebase
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.impact.shared.config.advanced import *
except ImportError:
    # Fallback configuration if import fails
    VECTOR_DB_PATH = "advanced_rag/vector_db"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromaDBExporter:
    """Export utility for ChromaDB collections"""
    
    def __init__(self, db_path: str = None, collection_name: str = "survey_responses"):
        self.db_path = db_path or VECTOR_DB_PATH
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        
    def initialize_chromadb(self) -> bool:
        """Initialize ChromaDB client and collection"""
        try:
            logger.info(f"🔧 Initializing ChromaDB from path: {self.db_path}")
            
            if not os.path.exists(self.db_path):
                logger.error(f"❌ ChromaDB path does not exist: {self.db_path}")
                return False
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # Get collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                doc_count = self.collection.count()
                logger.info(f"✅ Connected to collection '{self.collection_name}' with {doc_count} documents")
                return True
                
            except Exception as e:
                logger.error(f"❌ Collection '{self.collection_name}' not found: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {str(e)}")
            return False
    
    def export_all_documents(self) -> Optional[Dict[str, Any]]:
        """Export all documents from ChromaDB collection"""
        try:
            logger.info("📤 Exporting all documents from ChromaDB...")
            
            # Get all documents from collection
            results = self.collection.get(
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not results['ids']:
                logger.warning("⚠️ No documents found in collection")
                return None
            
            # Prepare export data
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "collection_name": self.collection_name,
                    "total_documents": len(results['ids']),
                    "embedding_dimension": len(results['embeddings'][0]) if results['embeddings'] else 0,
                    "source": "ChromaDB",
                    "version": "1.0"
                },
                "documents": []
            }
            
            # Process each document
            for i in range(len(results['ids'])):
                doc = {
                    "id": results['ids'][i],
                    "text": results['documents'][i] if results['documents'] else "",
                    "embedding": results['embeddings'][i] if results['embeddings'] else [],
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                }
                
                # Ensure metadata has required fields
                metadata = doc['metadata']
                doc['metadata'] = {
                    "charity_name": metadata.get('charity_name', ''),
                    "age_group": metadata.get('age_group', ''),
                    "gender": metadata.get('gender', ''),
                    "question_text": metadata.get('question_text', ''),
                    "question_type": metadata.get('question_type', ''),
                    "response_length": metadata.get('response_length', len(doc['text'])),
                    "original_response": metadata.get('original_response', ''),
                    "created_at": metadata.get('created_at', datetime.now().isoformat())
                }
                
                export_data["documents"].append(doc)
            
            logger.info(f"✅ Exported {len(export_data['documents'])} documents")
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export documents: {str(e)}")
            return None
    
    def save_export_to_file(self, export_data: Dict[str, Any], output_file: str) -> bool:
        """Save export data to JSON file"""
        try:
            logger.info(f"💾 Saving export data to: {output_file}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save to JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(output_file)
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"✅ Export saved successfully")
            logger.info(f"   File: {output_file}")
            logger.info(f"   Size: {file_size_mb:.2f} MB")
            logger.info(f"   Documents: {len(export_data['documents'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save export file: {str(e)}")
            return False
    
    def validate_export(self, export_data: Dict[str, Any]) -> bool:
        """Validate exported data integrity"""
        try:
            logger.info("🔍 Validating export data...")
            
            # Check basic structure
            required_keys = ['export_info', 'documents']
            for key in required_keys:
                if key not in export_data:
                    logger.error(f"❌ Missing required key: {key}")
                    return False
            
            documents = export_data['documents']
            if not documents:
                logger.error("❌ No documents in export")
                return False
            
            # Validate each document
            valid_docs = 0
            embedding_dims = set()
            
            for i, doc in enumerate(documents):
                # Check required fields
                required_doc_keys = ['id', 'text', 'embedding', 'metadata']
                missing_keys = [key for key in required_doc_keys if key not in doc]
                
                if missing_keys:
                    logger.warning(f"⚠️ Document {i} missing keys: {missing_keys}")
                    continue
                
                # Check embedding
                if doc['embedding'] and isinstance(doc['embedding'], list):
                    embedding_dims.add(len(doc['embedding']))
                
                # Check metadata
                metadata = doc['metadata']
                if not isinstance(metadata, dict):
                    logger.warning(f"⚠️ Document {i} has invalid metadata")
                    continue
                
                valid_docs += 1
            
            # Summary
            logger.info(f"✅ Validation complete:")
            logger.info(f"   Total documents: {len(documents)}")
            logger.info(f"   Valid documents: {valid_docs}")
            logger.info(f"   Embedding dimensions: {list(embedding_dims)}")
            
            if valid_docs == 0:
                logger.error("❌ No valid documents found")
                return False
            
            if len(embedding_dims) > 1:
                logger.warning(f"⚠️ Multiple embedding dimensions found: {embedding_dims}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {str(e)}")
            return False
    
    def export_sample(self, sample_size: int = 10) -> Optional[Dict[str, Any]]:
        """Export a sample of documents for testing"""
        try:
            logger.info(f"📤 Exporting sample of {sample_size} documents...")
            
            # Get sample documents
            results = self.collection.get(
                limit=sample_size,
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not results['ids']:
                logger.warning("⚠️ No documents found in collection")
                return None
            
            # Prepare sample export data
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "collection_name": self.collection_name,
                    "total_documents": len(results['ids']),
                    "sample_size": sample_size,
                    "embedding_dimension": len(results['embeddings'][0]) if results['embeddings'] else 0,
                    "source": "ChromaDB",
                    "version": "1.0",
                    "is_sample": True
                },
                "documents": []
            }
            
            # Process sample documents
            for i in range(len(results['ids'])):
                doc = {
                    "id": results['ids'][i],
                    "text": results['documents'][i] if results['documents'] else "",
                    "embedding": results['embeddings'][i] if results['embeddings'] else [],
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                }
                export_data["documents"].append(doc)
            
            logger.info(f"✅ Exported sample of {len(export_data['documents'])} documents")
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export sample: {str(e)}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection"""
        try:
            if not self.collection:
                return {"error": "Collection not initialized"}
            
            # Get basic stats
            total_count = self.collection.count()
            
            # Get sample to analyze
            sample = self.collection.get(limit=100, include=['documents', 'metadatas', 'embeddings'])
            
            stats = {
                "collection_name": self.collection_name,
                "total_documents": total_count,
                "sample_size": len(sample['ids']) if sample['ids'] else 0
            }
            
            if sample['embeddings']:
                stats["embedding_dimension"] = len(sample['embeddings'][0])
            
            # Analyze metadata
            if sample['metadatas']:
                metadata_keys = set()
                organizations = set()
                age_groups = set()
                question_types = set()
                
                for metadata in sample['metadatas']:
                    if metadata:
                        metadata_keys.update(metadata.keys())
                        organizations.add(metadata.get('charity_name', ''))
                        age_groups.add(metadata.get('age_group', ''))
                        question_types.add(metadata.get('question_type', ''))
                
                stats.update({
                    "metadata_keys": list(metadata_keys),
                    "unique_organizations": len(organizations),
                    "unique_age_groups": len(age_groups),
                    "unique_question_types": len(question_types),
                    "sample_organizations": list(organizations)[:10],
                    "sample_age_groups": list(age_groups),
                    "sample_question_types": list(question_types)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {str(e)}")
            return {"error": str(e)}


def main():
    """Main export function"""
    print("🚀 ChromaDB Export Utility")
    print("=" * 50)
    
    # Initialize exporter
    exporter = ChromaDBExporter()
    
    # Initialize ChromaDB
    if not exporter.initialize_chromadb():
        print("❌ Failed to initialize ChromaDB. Exiting.")
        return
    
    # Get collection stats
    print("\n📊 Collection Statistics:")
    stats = exporter.get_collection_stats()
    for key, value in stats.items():
        if key != "error":
            print(f"   {key}: {value}")
    
    # Ask user what to export
    print("\n🤔 What would you like to export?")
    print("1. Full export (all documents)")
    print("2. Sample export (10 documents)")
    print("3. Custom sample size")
    print("4. Just show stats and exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    export_data = None
    output_file = None
    
    if choice == "1":
        # Full export
        export_data = exporter.export_all_documents()
        output_file = "vercel-deployment/data/chromadb_full_export.json"
        
    elif choice == "2":
        # Sample export
        export_data = exporter.export_sample(10)
        output_file = "vercel-deployment/data/chromadb_sample_export.json"
        
    elif choice == "3":
        # Custom sample
        try:
            sample_size = int(input("Enter sample size: "))
            export_data = exporter.export_sample(sample_size)
            output_file = f"vercel-deployment/data/chromadb_sample_{sample_size}_export.json"
        except ValueError:
            print("❌ Invalid sample size")
            return
            
    elif choice == "4":
        # Just stats
        print("✅ Stats displayed above. Exiting.")
        return
        
    else:
        print("❌ Invalid choice")
        return
    
    # Process export
    if export_data:
        # Validate export
        if exporter.validate_export(export_data):
            # Save to file
            if exporter.save_export_to_file(export_data, output_file):
                print(f"\n✅ Export completed successfully!")
                print(f"   Output file: {output_file}")
                print(f"   Documents exported: {len(export_data['documents'])}")
                
                # Show next steps
                print(f"\n📋 Next Steps:")
                print(f"1. Review the export file: {output_file}")
                print(f"2. Run the Pinecone migration script:")
                print(f"   python vercel-deployment/scripts/migrate_to_pinecone.py")
            else:
                print("❌ Failed to save export file")
        else:
            print("❌ Export validation failed")
    else:
        print("❌ Export failed")


if __name__ == "__main__":
    main()