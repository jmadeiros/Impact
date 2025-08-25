"""
Unit tests for Vector Store Clients
Tests Pinecone and Supabase clients, factory pattern, and error handling
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from typing import List, Dict, Any

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from vector_client import (
    PineconeVectorClient, SupabaseVectorClient, VectorStoreFactory,
    calculate_similarity, batch_process
)


class TestPineconeVectorClient(unittest.TestCase):
    """Test cases for PineconeVectorClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "api_key": "test_api_key",
            "environment": "test_env",
            "index_name": "test_index",
            "namespace": "test_namespace"
        }
    
    @patch('pinecone.Pinecone')
    def test_initialization_success(self, mock_pinecone_class):
        """Test successful Pinecone client initialization"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        client = PineconeVectorClient(**self.test_config)
        
        self.assertEqual(client.api_key, "test_api_key")
        self.assertEqual(client.environment, "test_env")
        self.assertEqual(client.index_name, "test_index")
        self.assertEqual(client.namespace, "test_namespace")
        self.assertEqual(client.index, mock_index)
        
        mock_pinecone_class.assert_called_once_with(api_key="test_api_key")
        mock_pinecone.Index.assert_called_once_with("test_index")
    
    @patch('pinecone.Pinecone')
    def test_initialization_failure(self, mock_pinecone_class):
        """Test Pinecone client initialization failure"""
        mock_pinecone_class.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception):
            PineconeVectorClient(**self.test_config)
    
    @patch('pinecone.Pinecone')
    def test_search_success(self, mock_pinecone_class):
        """Test successful vector search"""
        # Mock Pinecone setup
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        # Mock search results
        mock_match = Mock()
        mock_match.id = "doc1"
        mock_match.score = 0.95
        mock_match.metadata = {
            "text": "Test document content",
            "charity_name": "Test Org",
            "age_group": "16-18",
            "gender": "Female",
            "question_text": "Test question"
        }
        
        mock_results = Mock()
        mock_results.matches = [mock_match]
        mock_index.query.return_value = mock_results
        
        client = PineconeVectorClient(**self.test_config)
        
        # Test search
        query_embedding = [0.1, 0.2, 0.3]
        results = client.search(query_embedding, top_k=5)
        
        # Verify results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["id"], "doc1")
        self.assertEqual(result["score"], 0.95)
        self.assertEqual(result["text"], "Test document content")
        self.assertEqual(result["organization"], "Test Org")
        self.assertEqual(result["age_group"], "16-18")
        
        # Verify query parameters
        mock_index.query.assert_called_once_with(
            vector=query_embedding,
            top_k=5,
            namespace="test_namespace",
            include_metadata=True,
            include_values=False
        )
    
    @patch('pinecone.Pinecone')
    def test_search_with_filters(self, mock_pinecone_class):
        """Test vector search with filters"""
        # Mock Pinecone setup
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        mock_results = Mock()
        mock_results.matches = []
        mock_index.query.return_value = mock_results
        
        client = PineconeVectorClient(**self.test_config)
        
        # Test search with filters
        query_embedding = [0.1, 0.2, 0.3]
        filters = {"age_group": ["16-18"], "organization": "Test Org"}
        client.search(query_embedding, top_k=3, filters=filters)
        
        # Verify filters were converted correctly
        expected_filter = {
            "age_group": {"$in": ["16-18"]},
            "organization": "Test Org"
        }
        
        mock_index.query.assert_called_once_with(
            vector=query_embedding,
            top_k=3,
            namespace="test_namespace",
            include_metadata=True,
            include_values=False,
            filter=expected_filter
        )
    
    @patch('pinecone.Pinecone')
    def test_search_empty_embedding(self, mock_pinecone_class):
        """Test search with empty embedding"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        client = PineconeVectorClient(**self.test_config)
        
        # Test with empty embedding - should raise ServerlessError
        with self.assertRaises(Exception):  # ServerlessError if available
            client.search([], top_k=5)
    
    @patch('pinecone.Pinecone')
    def test_upsert_success(self, mock_pinecone_class):
        """Test successful document upsert"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        client = PineconeVectorClient(**self.test_config)
        
        # Test documents
        documents = [
            {
                "id": "doc1",
                "text": "Test document 1",
                "embedding": [0.1, 0.2, 0.3],
                "charity_name": "Test Org",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "Test question",
                "question_type": "open",
                "created_at": "2024-01-01"
            }
        ]
        
        result = client.upsert(documents)
        
        self.assertTrue(result)
        mock_index.upsert.assert_called_once()
        
        # Verify upsert data structure
        call_args = mock_index.upsert.call_args[1]
        vectors = call_args["vectors"]
        self.assertEqual(len(vectors), 1)
        self.assertEqual(vectors[0]["id"], "doc1")
        self.assertEqual(vectors[0]["values"], [0.1, 0.2, 0.3])
        self.assertEqual(vectors[0]["metadata"]["text"], "Test document 1")
    
    @patch('pinecone.Pinecone')
    def test_upsert_batch_processing(self, mock_pinecone_class):
        """Test upsert with batch processing"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        client = PineconeVectorClient(**self.test_config)
        
        # Create 150 documents to test batching (batch size is 100)
        documents = []
        for i in range(150):
            documents.append({
                "id": f"doc{i}",
                "text": f"Test document {i}",
                "embedding": [0.1, 0.2, 0.3],
                "charity_name": "Test Org"
            })
        
        result = client.upsert(documents)
        
        self.assertTrue(result)
        # Should be called twice due to batching
        self.assertEqual(mock_index.upsert.call_count, 2)
    
    @patch('pinecone.Pinecone')
    def test_delete_success(self, mock_pinecone_class):
        """Test successful document deletion"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        client = PineconeVectorClient(**self.test_config)
        
        ids = ["doc1", "doc2", "doc3"]
        result = client.delete(ids)
        
        self.assertTrue(result)
        mock_index.delete.assert_called_once_with(ids=ids, namespace="test_namespace")
    
    @patch('pinecone.Pinecone')
    def test_get_stats(self, mock_pinecone_class):
        """Test statistics retrieval"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        # Mock stats
        mock_stats = Mock()
        mock_stats.total_vector_count = 1000
        mock_stats.dimension = 384
        mock_stats.index_fullness = 0.02
        mock_stats.namespaces = {"test_namespace": Mock()}
        mock_index.describe_index_stats.return_value = mock_stats
        
        client = PineconeVectorClient(**self.test_config)
        
        stats = client.get_stats()
        
        self.assertEqual(stats["total_vectors"], 1000)
        self.assertEqual(stats["dimension"], 384)
        self.assertEqual(stats["index_fullness"], 0.02)
        self.assertEqual(stats["vector_store_type"], "pinecone")
        self.assertEqual(stats["index_name"], "test_index")
    
    @patch('pinecone.Pinecone')
    def test_health_check_success(self, mock_pinecone_class):
        """Test successful health check"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        # Mock successful query
        mock_results = Mock()
        mock_results.matches = []
        mock_index.query.return_value = mock_results
        
        client = PineconeVectorClient(**self.test_config)
        
        health = client.health_check()
        
        self.assertTrue(health)
        mock_index.query.assert_called_once()
    
    @patch('pinecone.Pinecone')
    def test_health_check_failure(self, mock_pinecone_class):
        """Test health check failure"""
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        # Mock query failure
        mock_index.query.side_effect = Exception("Connection failed")
        
        client = PineconeVectorClient(**self.test_config)
        
        health = client.health_check()
        
        self.assertFalse(health)
    
    def test_convert_filters(self):
        """Test filter conversion for Pinecone format"""
        client = PineconeVectorClient(**self.test_config)
        
        # Test list values
        filters = {"age_group": ["16-18", "19-25"], "gender": ["Male"]}
        converted = client._convert_filters(filters)
        
        expected = {
            "age_group": {"$in": ["16-18", "19-25"]},
            "gender": {"$in": ["Male"]}
        }
        self.assertEqual(converted, expected)
        
        # Test single values
        filters = {"organization": "Test Org"}
        converted = client._convert_filters(filters)
        
        expected = {"organization": "Test Org"}
        self.assertEqual(converted, expected)


class TestSupabaseVectorClient(unittest.TestCase):
    """Test cases for SupabaseVectorClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "url": "https://test.supabase.co",
            "key": "test_key",
            "table_name": "test_vectors"
        }
    
    @patch('supabase.create_client')
    def test_initialization_success(self, mock_create_client):
        """Test successful Supabase client initialization"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        self.assertEqual(client.url, "https://test.supabase.co")
        self.assertEqual(client.key, "test_key")
        self.assertEqual(client.table_name, "test_vectors")
        self.assertEqual(client.client, mock_client)
        
        mock_create_client.assert_called_once_with("https://test.supabase.co", "test_key")
    
    @patch('supabase.create_client')
    def test_search_success(self, mock_create_client):
        """Test successful vector search"""
        mock_client = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        # Mock query chain
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Mock results
        mock_results = Mock()
        mock_results.data = [
            {
                "id": "doc1",
                "text": "Test document",
                "charity_name": "Test Org",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "Test question"
            }
        ]
        mock_query.execute.return_value = mock_results
        
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        # Test search
        query_embedding = [0.1, 0.2, 0.3]
        results = client.search(query_embedding, top_k=5)
        
        # Verify results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["id"], "doc1")
        self.assertEqual(result["text"], "Test document")
        self.assertEqual(result["organization"], "Test Org")
        
        # Verify query was built correctly
        mock_client.table.assert_called_once_with("test_vectors")
        mock_table.select.assert_called_once_with("*")
        mock_query.limit.assert_called_once_with(5)
    
    @patch('supabase.create_client')
    def test_search_with_filters(self, mock_create_client):
        """Test vector search with filters"""
        mock_client = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        # Mock query chain
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = Mock(data=[])
        
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        # Test search with filters
        query_embedding = [0.1, 0.2, 0.3]
        filters = {"age_group": ["16-18"], "organization": "Test Org"}
        client.search(query_embedding, filters=filters)
        
        # Verify filters were applied
        mock_query.in_.assert_called_once_with("age_group", ["16-18"])
        mock_query.eq.assert_called_once_with("organization", "Test Org")
    
    @patch('supabase.create_client')
    def test_upsert_success(self, mock_create_client):
        """Test successful document upsert"""
        mock_client = Mock()
        mock_table = Mock()
        mock_upsert = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()
        
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        # Test documents
        documents = [
            {
                "id": "doc1",
                "text": "Test document",
                "embedding": [0.1, 0.2, 0.3],
                "charity_name": "Test Org",
                "age_group": "16-18"
            }
        ]
        
        result = client.upsert(documents)
        
        self.assertTrue(result)
        mock_table.upsert.assert_called_once()
        
        # Verify upsert data
        call_args = mock_table.upsert.call_args[0][0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0]["id"], "doc1")
        self.assertEqual(call_args[0]["text"], "Test document")
        self.assertEqual(call_args[0]["embedding"], [0.1, 0.2, 0.3])
    
    @patch('supabase.create_client')
    def test_delete_success(self, mock_create_client):
        """Test successful document deletion"""
        mock_client = Mock()
        mock_table = Mock()
        mock_delete = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.in_.return_value = mock_delete
        mock_delete.execute.return_value = Mock()
        
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        ids = ["doc1", "doc2"]
        result = client.delete(ids)
        
        self.assertTrue(result)
        mock_table.delete.assert_called_once()
        mock_delete.in_.assert_called_once_with("id", ids)
    
    @patch('supabase.create_client')
    def test_get_stats(self, mock_create_client):
        """Test statistics retrieval"""
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.execute.return_value = Mock(count=1000)
        
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        stats = client.get_stats()
        
        self.assertEqual(stats["total_vectors"], 1000)
        self.assertEqual(stats["vector_store_type"], "supabase")
        self.assertEqual(stats["table_name"], "test_vectors")
    
    @patch('supabase.create_client')
    def test_health_check_success(self, mock_create_client):
        """Test successful health check"""
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_select
        mock_select.execute.return_value = Mock()
        
        mock_create_client.return_value = mock_client
        
        client = SupabaseVectorClient(**self.test_config)
        
        health = client.health_check()
        
        self.assertTrue(health)
        mock_table.select.assert_called_once_with("id")
        mock_select.limit.assert_called_once_with(1)


class TestVectorStoreFactory(unittest.TestCase):
    """Test cases for VectorStoreFactory"""
    
    @patch('vector_client.PineconeVectorClient')
    def test_create_pinecone_client(self, mock_pinecone_class):
        """Test creating Pinecone client via factory"""
        mock_client = Mock()
        mock_pinecone_class.return_value = mock_client
        
        config = {
            "vector_store_type": "pinecone",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index",
            "pinecone_namespace": "test_ns"
        }
        
        client = VectorStoreFactory.create_client(config)
        
        self.assertEqual(client, mock_client)
        mock_pinecone_class.assert_called_once_with(
            api_key="test_key",
            environment="test_env",
            index_name="test_index",
            namespace="test_ns"
        )
    
    @patch('vector_client.SupabaseVectorClient')
    def test_create_supabase_client(self, mock_supabase_class):
        """Test creating Supabase client via factory"""
        mock_client = Mock()
        mock_supabase_class.return_value = mock_client
        
        config = {
            "vector_store_type": "supabase",
            "supabase_url": "https://test.supabase.co",
            "supabase_key": "test_key",
            "supabase_table": "test_table"
        }
        
        client = VectorStoreFactory.create_client(config)
        
        self.assertEqual(client, mock_client)
        mock_supabase_class.assert_called_once_with(
            url="https://test.supabase.co",
            key="test_key",
            table_name="test_table"
        )
    
    def test_create_client_invalid_type(self):
        """Test creating client with invalid type"""
        config = {"vector_store_type": "invalid"}
        
        with self.assertRaises(ValueError) as context:
            VectorStoreFactory.create_client(config)
        
        self.assertIn("Unsupported vector store type", str(context.exception))
    
    def test_create_pinecone_missing_config(self):
        """Test creating Pinecone client with missing configuration"""
        config = {
            "vector_store_type": "pinecone",
            "pinecone_api_key": "test_key"
            # Missing environment and index_name
        }
        
        with self.assertRaises(ValueError) as context:
            VectorStoreFactory.create_client(config)
        
        self.assertIn("Missing required Pinecone configuration", str(context.exception))
    
    def test_create_supabase_missing_config(self):
        """Test creating Supabase client with missing configuration"""
        config = {
            "vector_store_type": "supabase",
            "supabase_url": "https://test.supabase.co"
            # Missing supabase_key
        }
        
        with self.assertRaises(ValueError) as context:
            VectorStoreFactory.create_client(config)
        
        self.assertIn("Missing required Supabase configuration", str(context.exception))
    
    @patch.dict(os.environ, {
        "VECTOR_STORE_TYPE": "pinecone",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('vector_client.PineconeVectorClient')
    def test_create_from_env(self, mock_pinecone_class):
        """Test creating client from environment variables"""
        mock_client = Mock()
        mock_pinecone_class.return_value = mock_client
        
        client = VectorStoreFactory.create_from_env()
        
        self.assertEqual(client, mock_client)
        mock_pinecone_class.assert_called_once()


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        similarity = calculate_similarity(vec1, vec2)
        
        self.assertAlmostEqual(similarity, 1.0, places=5)
    
    def test_calculate_similarity_orthogonal(self):
        """Test similarity calculation for orthogonal vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = calculate_similarity(vec1, vec2)
        
        self.assertAlmostEqual(similarity, 0.0, places=5)
    
    def test_calculate_similarity_opposite(self):
        """Test similarity calculation for opposite vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        
        similarity = calculate_similarity(vec1, vec2)
        
        self.assertAlmostEqual(similarity, -1.0, places=5)
    
    def test_calculate_similarity_zero_vector(self):
        """Test similarity calculation with zero vector"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        similarity = calculate_similarity(vec1, vec2)
        
        self.assertEqual(similarity, 0.0)
    
    def test_batch_process_small_batch(self):
        """Test batch processing with small batch size"""
        items = list(range(10))
        batches = list(batch_process(items, batch_size=3))
        
        self.assertEqual(len(batches), 4)  # 3 + 3 + 3 + 1
        self.assertEqual(batches[0], [0, 1, 2])
        self.assertEqual(batches[1], [3, 4, 5])
        self.assertEqual(batches[2], [6, 7, 8])
        self.assertEqual(batches[3], [9])
    
    def test_batch_process_exact_batch(self):
        """Test batch processing with exact batch size"""
        items = list(range(6))
        batches = list(batch_process(items, batch_size=3))
        
        self.assertEqual(len(batches), 2)
        self.assertEqual(batches[0], [0, 1, 2])
        self.assertEqual(batches[1], [3, 4, 5])
    
    def test_batch_process_empty_list(self):
        """Test batch processing with empty list"""
        items = []
        batches = list(batch_process(items, batch_size=3))
        
        self.assertEqual(len(batches), 0)


if __name__ == '__main__':
    unittest.main()