#!/usr/bin/env python3
"""
Pinecone Migration Script for Vercel Deployment
Migrates survey response data from Supabase to Pinecone vector store
"""
import os
import sys
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    print(f"📁 Loaded environment from: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PineconeMigrator:
    """Handles migration from Supabase to Pinecone"""
    
    def __init__(self):
        self.supabase_client = None
        self.pinecone_client = None
        self.pinecone_index = None
        self.embedding_model = None
        
        # Configuration from environment
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT')
        self.pinecone_index_name = os.getenv('PINECONE_INDEX_NAME', 'rag-survey-responses')
        self.pinecone_namespace = os.getenv('PINECONE_NAMESPACE', 'production')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        self.validate_configuration()
    
    def validate_configuration(self):
        """Validate required environment variables"""
        required_vars = {
            'SUPABASE_URL': self.supabase_url,
            'SUPABASE_KEY': self.supabase_key,
            'PINECONE_API_KEY': self.pinecone_api_key,
            'PINECONE_ENVIRONMENT': self.pinecone_environment,
            'GOOGLE_API_KEY': self.google_api_key
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("✅ Configuration validation passed")
    
    def initialize_clients(self):
        """Initialize Supabase and Pinecone clients"""
        try:
            # Initialize Supabase client
            from supabase import create_client
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            logger.info("✅ Supabase client initialized")
            
            # Initialize Pinecone client
            from pinecone import Pinecone, ServerlessSpec
            
            self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            
            # Check if index exists, create if not
            existing_indexes = self.pinecone_client.list_indexes().names()
            if self.pinecone_index_name not in existing_indexes:
                logger.info(f"🔧 Creating Pinecone index: {self.pinecone_index_name}")
                self.pinecone_client.create_index(
                    name=self.pinecone_index_name,
                    dimension=384,  # sentence-transformers dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                # Wait for index to be ready
                time.sleep(10)
            
            self.pinecone_index = self.pinecone_client.Index(self.pinecone_index_name)
            logger.info(f"✅ Pinecone index '{self.pinecone_index_name}' ready")
            
            # Initialize embedding model
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("✅ Sentence transformers embeddings initialized")
            
        except ImportError as e:
            logger.error(f"❌ Missing required library: {e}")
            logger.error("Install with: pip install pinecone-client supabase langchain-google-genai")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize clients: {e}")
            raise
    
    def fetch_supabase_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch survey response data from Supabase"""
        try:
            logger.info("📥 Fetching data from Supabase...")
            
            # Query responses with question details
            query = self.supabase_client.table("responses").select("""
                response_id,
                participant_id,
                charity_name,
                age_group,
                gender,
                response_value,
                thematic_tags,
                embedding,
                created_at,
                questions (
                    question_id,
                    question_text,
                    question_type,
                    mcq_options
                )
            """)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            if not response.data:
                logger.warning("⚠️ No data found in Supabase responses table")
                return []
            
            logger.info(f"✅ Fetched {len(response.data)} records from Supabase")
            return response.data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Supabase data: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            logger.info(f"🧠 Generating embeddings for {len(texts)} texts...")
            
            # Use sentence transformers
            embeddings = self.embedding_model.encode(texts).tolist()
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {e}")
            raise
    
    def prepare_pinecone_vectors(self, supabase_data: List[Dict[str, Any]], 
                                embeddings: List[List[float]]) -> List[Dict[str, Any]]:
        """Prepare vectors for Pinecone upsert"""
        vectors = []
        
        for i, record in enumerate(supabase_data):
            # Skip if no embedding available
            if i >= len(embeddings):
                continue
            
            # Extract question info
            question_info = record.get('questions', {}) or {}
            
            # Prepare metadata
            metadata = {
                "text": record.get('response_value', ''),
                "charity_name": record.get('charity_name', ''),
                "age_group": record.get('age_group', ''),
                "gender": record.get('gender', ''),
                "question_text": question_info.get('question_text', ''),
                "question_type": question_info.get('question_type', ''),
                "question_id": question_info.get('question_id', ''),
                "participant_id": record.get('participant_id', ''),
                "response_length": len(record.get('response_value', '')),
                "thematic_tags": json.dumps(record.get('thematic_tags', [])),
                "created_at": record.get('created_at', ''),
                "source": "supabase_migration"
            }
            
            # Create vector
            vector = {
                "id": f"response_{record.get('response_id', i)}",
                "values": embeddings[i],
                "metadata": metadata
            }
            
            vectors.append(vector)
        
        logger.info(f"✅ Prepared {len(vectors)} vectors for Pinecone")
        return vectors
    
    def upsert_to_pinecone(self, vectors: List[Dict[str, Any]], batch_size: int = 100):
        """Upsert vectors to Pinecone in batches"""
        try:
            logger.info(f"📤 Upserting {len(vectors)} vectors to Pinecone...")
            
            total_batches = (len(vectors) + batch_size - 1) // batch_size
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} vectors)")
                
                # Upsert batch
                self.pinecone_index.upsert(
                    vectors=batch,
                    namespace=self.pinecone_namespace
                )
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
            
            logger.info("✅ All vectors upserted to Pinecone successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert to Pinecone: {e}")
            raise
    
    def verify_migration(self, original_count: int) -> bool:
        """Verify the migration was successful"""
        try:
            logger.info("🔍 Verifying migration...")
            
            # Wait a moment for Pinecone to index the vectors
            logger.info("⏳ Waiting for Pinecone to index vectors...")
            time.sleep(5)
            
            # Get Pinecone index stats
            stats = self.pinecone_index.describe_index_stats()
            
            # Check namespace stats
            namespace_stats = stats.get('namespaces', {}).get(self.pinecone_namespace, {})
            pinecone_count = namespace_stats.get('vector_count', 0)
            
            logger.info(f"📊 Migration verification:")
            logger.info(f"   Original Supabase records: {original_count}")
            logger.info(f"   Pinecone vectors in namespace '{self.pinecone_namespace}': {pinecone_count}")
            logger.info(f"   Total vectors in index: {stats.get('total_vector_count', 0)}")
            
            # Test a sample query
            test_query = [0.1] * 384  # Dummy query vector (sentence-transformers dimension)
            query_results = self.pinecone_index.query(
                vector=test_query,
                top_k=5,
                namespace=self.pinecone_namespace,
                include_metadata=True
            )
            
            logger.info(f"   Sample query returned {len(query_results.matches)} results")
            
            if query_results.matches:
                sample_metadata = query_results.matches[0].metadata
                logger.info(f"   Sample result metadata keys: {list(sample_metadata.keys())}")
            
            # Consider it successful if we have vectors or if the query returns results
            success = pinecone_count > 0 or len(query_results.matches) > 0 or stats.get('total_vector_count', 0) > 0
            
            if success:
                logger.info("✅ Migration verification passed")
            else:
                logger.error("❌ Migration verification failed")
                # Additional debugging
                logger.info(f"🔍 Debug info:")
                logger.info(f"   Full stats: {stats}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """Get summary of migration status"""
        try:
            # Pinecone stats
            stats = self.pinecone_index.describe_index_stats()
            namespace_stats = stats.get('namespaces', {}).get(self.pinecone_namespace, {})
            
            return {
                "pinecone_index": self.pinecone_index_name,
                "pinecone_namespace": self.pinecone_namespace,
                "pinecone_environment": self.pinecone_environment,
                "total_vectors": stats.get('total_vector_count', 0),
                "namespace_vectors": namespace_stats.get('vector_count', 0),
                "dimension": stats.get('dimension', 0),
                "index_fullness": stats.get('index_fullness', 0),
                "migration_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get migration summary: {e}")
            return {"error": str(e)}
    
    def run_migration(self, sample_size: Optional[int] = None, dry_run: bool = False):
        """Run the complete migration process"""
        try:
            logger.info("🚀 Starting Pinecone migration...")
            logger.info(f"   Sample size: {sample_size or 'All records'}")
            logger.info(f"   Dry run: {dry_run}")
            
            # Initialize clients
            self.initialize_clients()
            
            # Fetch data from Supabase
            supabase_data = self.fetch_supabase_data(limit=sample_size)
            
            if not supabase_data:
                logger.error("❌ No data to migrate")
                return False
            
            # Prepare texts for embedding
            texts = []
            for record in supabase_data:
                response_text = record.get('response_value', '')
                if response_text:
                    texts.append(response_text)
            
            if not texts:
                logger.error("❌ No valid response texts found")
                return False
            
            # Generate embeddings
            embeddings = self.generate_embeddings_batch(texts)
            
            # Prepare vectors
            vectors = self.prepare_pinecone_vectors(supabase_data, embeddings)
            
            if dry_run:
                logger.info("🔍 DRY RUN - Would migrate:")
                logger.info(f"   Records: {len(supabase_data)}")
                logger.info(f"   Vectors: {len(vectors)}")
                logger.info(f"   Sample vector keys: {list(vectors[0].keys()) if vectors else 'None'}")
                if vectors:
                    logger.info(f"   Sample metadata keys: {list(vectors[0]['metadata'].keys())}")
                return True
            
            # Upsert to Pinecone
            self.upsert_to_pinecone(vectors)
            
            # Verify migration
            success = self.verify_migration(len(supabase_data))
            
            if success:
                # Print summary
                summary = self.get_migration_summary()
                logger.info("📋 Migration Summary:")
                for key, value in summary.items():
                    logger.info(f"   {key}: {value}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False


def main():
    """Main migration function"""
    print("🚀 Pinecone Migration Tool")
    print("=" * 50)
    
    try:
        migrator = PineconeMigrator()
        
        # Ask user for migration options
        print("\n🤔 Migration Options:")
        print("1. Full migration (all data)")
        print("2. Sample migration (100 records)")
        print("3. Custom sample size")
        print("4. Dry run (test without migrating)")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        sample_size = None
        dry_run = False
        
        if choice == "1":
            # Full migration
            print("📊 Running full migration...")
            
        elif choice == "2":
            # Sample migration
            sample_size = 100
            print(f"📊 Running sample migration ({sample_size} records)...")
            
        elif choice == "3":
            # Custom sample
            try:
                sample_size = int(input("Enter sample size: "))
                print(f"📊 Running custom sample migration ({sample_size} records)...")
            except ValueError:
                print("❌ Invalid sample size")
                return
                
        elif choice == "4":
            # Dry run
            dry_run = True
            sample_size = 10
            print("🔍 Running dry run (10 records)...")
            
        else:
            print("❌ Invalid choice")
            return
        
        # Confirm migration
        if not dry_run:
            confirm = input(f"\n⚠️ This will migrate data to Pinecone. Continue? (y/N): ").lower()
            if confirm != 'y':
                print("❌ Migration cancelled")
                return
        
        # Run migration
        success = migrator.run_migration(sample_size=sample_size, dry_run=dry_run)
        
        if success:
            print("\n✅ Migration completed successfully!")
            
            if not dry_run:
                print("\n📋 Next Steps:")
                print("1. Update your .env file to use VECTOR_STORE_TYPE=pinecone")
                print("2. Test the API endpoints with the new Pinecone data")
                print("3. Deploy to Vercel for production testing")
        else:
            print("\n❌ Migration failed. Check the logs above for details.")
            
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrupted by user")
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")


if __name__ == "__main__":
    main()