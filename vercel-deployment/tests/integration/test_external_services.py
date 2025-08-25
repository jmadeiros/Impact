"""
Integration tests for external service integration
Tests real integration with external services (when available) or comprehensive mocking
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import time
from typing import List, Dict, Any

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from rag_engine import ServerlessRAGEngine
from vector_client import VectorStoreFactory, PineconeVectorClient, SupabaseVectorClient
from embeddings import ServerlessEmbeddingClient
from conversation import ConversationalRAGAdapter


class TestVectorStoreIntegration(unittest.TestCase):
    """Integration tests for vector store services"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index",
            "pinecone_namespace": "test_namespace",
            "supabase_url": "https://test.supabase.co",
            "supabase_key": "test_key",
            "vector_store_type": "pinecone"
        }
        
        self.test_documents = [
            {
                "id": "doc1",
                "text": "Programs help build confidence through structured activities.",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 77,  # 385 dimensions
                "charity_name": "YCUK",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "How do programs help?",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
    
    @patch('vector_client.Pinecone')
    def test_pinecone_integration_full_workflow(self, mock_pinecone_class):
        """Test complete Pinecone integration workflow"""
        # Mock Pinecone client and index
        mock_pinecone = Mock()
        mock_index = Mock()
        mock_pinecone.Index.return_value = mock_index
        mock_pinecone_class.return_value = mock_pinecone
        
        # Mock search results
        mock_match = Mock()
        mock_match.id = "doc1"
        mock_match.score = 0.95
        mock_match.metadata = {
            "text": "Programs help build confidence through structured activities.",
            "charity_name": "YCUK",
            "age_group": "16-18",
            "gender": "Female",
            "question_text": "How do programs help?"
        }
        
        mock_results = Mock()
        mock_results.matches = [mock_match]
        mock_index.query.return_value = mock_results
        
        # Mock stats
        mock_stats = Mock()
        mock_stats.total_vector_count = 1000
        mock_stats.dimension = 384
        mock_stats.index_fullness = 0.02
        mock_stats.namespaces = {"test_namespace": Mock()}
        mock_index.describe_index_stats.return_value = mock_stats
        
        # Create client
        client = PineconeVectorClient(
            api_key=self.test_config["pinecone_api_key"],
            environment=self.test_config["pinecone_environment"],
            index_name=self.test_config["pinecone_index_name"],
            namespace=self.test_config["pinecone_namespace"]
        )
        
        # Test upsert
        upsert_result = client.upsert(self.test_documents)
        self.assertTrue(upsert_result)
        mock_index.upsert.assert_called_once()
        
        # Test search
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 77
        search_results = client.search(query_embedding, top_k=5)
        
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]["id"], "doc1")
        self.assertEqual(search_results[0]["score"], 0.95)
        self.assertEqual(search_results[0]["organization"], "YCUK")
        
        # Test health check
        health = client.health_check()
        self.assertTrue(health)
        
        # Test stats
        stats = client.get_stats()
        self.assertEqual(stats["total_vectors"], 1000)
        self.assertEqual(stats["vector_store_type"], "pinecone")
        
        # Test delete
        delete_result = client.delete(["doc1"])
        self.assertTrue(delete_result)
        mock_index.delete.assert_called_once_with(ids=["doc1"], namespace="test_namespace")
    
    @patch('vector_client.create_client')
    def test_supabase_integration_full_workflow(self, mock_create_client):
        """Test complete Supabase integration workflow"""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_query
        mock_table.upsert.return_value = mock_query
        mock_table.delete.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.execute.return_value = Mock(data=[], count=500)
        
        mock_create_client.return_value = mock_client
        
        # Create client
        client = SupabaseVectorClient(
            url=self.test_config["supabase_url"],
            key=self.test_config["supabase_key"]
        )
        
        # Test upsert
        upsert_result = client.upsert(self.test_documents)
        self.assertTrue(upsert_result)
        mock_table.upsert.assert_called_once()
        
        # Test search
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 77
        search_results = client.search(query_embedding, top_k=5)
        
        # Should return empty results from mock
        self.assertEqual(len(search_results), 0)
        mock_table.select.assert_called_once_with("*")
        
        # Test health check
        health = client.health_check()
        self.assertTrue(health)
        
        # Test stats
        stats = client.get_stats()
        self.assertEqual(stats["total_vectors"], 500)
        self.assertEqual(stats["vector_store_type"], "supabase")
        
        # Test delete
        delete_result = client.delete(["doc1"])
        self.assertTrue(delete_result)
        mock_table.delete.assert_called_once()
    
    def test_vector_store_factory_integration(self):
        """Test vector store factory with different configurations"""
        # Test Pinecone factory
        with patch('vector_client.PineconeVectorClient') as mock_pinecone:
            mock_client = Mock()
            mock_pinecone.return_value = mock_client
            
            config = self.test_config.copy()
            config["vector_store_type"] = "pinecone"
            
            client = VectorStoreFactory.create_client(config)
            
            self.assertEqual(client, mock_client)
            mock_pinecone.assert_called_once_with(
                api_key="test_key",
                environment="test_env",
                index_name="test_index",
                namespace="test_namespace"
            )
        
        # Test Supabase factory
        with patch('vector_client.SupabaseVectorClient') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            config = self.test_config.copy()
            config["vector_store_type"] = "supabase"
            
            client = VectorStoreFactory.create_client(config)
            
            self.assertEqual(client, mock_client)
            mock_supabase.assert_called_once_with(
                url="https://test.supabase.co",
                key="test_key",
                table_name="vector_documents"
            )
    
    def test_vector_store_error_handling(self):
        """Test vector store error handling and fallback behavior"""
        # Test missing configuration
        with self.assertRaises(ValueError):
            VectorStoreFactory.create_client({"vector_store_type": "pinecone"})
        
        # Test invalid vector store type
        with self.assertRaises(ValueError):
            VectorStoreFactory.create_client({"vector_store_type": "invalid"})


class TestLLMIntegration(unittest.TestCase):
    """Integration tests for LLM services"""
    
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_google_llm_integration(self, mock_llm_class):
        """Test Google Gemini LLM integration"""
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Based on survey data, programs build confidence through structured activities and peer support."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        # Create RAG engine
        config = {
            "google_api_key": "test_key",
            "llm_model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        engine = ServerlessRAGEngine(config)
        
        # Test LLM initialization
        llm = engine.llm
        self.assertEqual(llm, mock_llm)
        
        mock_llm_class.assert_called_once_with(
            model="gemini-1.5-flash",
            google_api_key="test_key",
            temperature=0.1,
            max_tokens=1000
        )
        
        # Test response generation
        context_docs = [
            {
                "text": "Programs help build confidence",
                "organization": "YCUK",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "How do programs help?"
            }
        ]
        
        response = engine.generate_response("How do programs build confidence?", context_docs)
        
        self.assertIn("programs build confidence", response.lower())
        mock_llm.invoke.assert_called_once()
    
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_llm_error_handling(self, mock_llm_class):
        """Test LLM error handling"""
        # Mock LLM that raises exception
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("API rate limit exceeded")
        mock_llm_class.return_value = mock_llm
        
        config = {
            "google_api_key": "test_key",
            "llm_model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        engine = ServerlessRAGEngine(config)
        
        # Should raise ServerlessError or handle gracefully
        with self.assertRaises(Exception):
            engine.generate_response("test query", [])


class TestEmbeddingIntegration(unittest.TestCase):
    """Integration tests for embedding services"""
    
    @patch('embeddings.SentenceTransformer')
    def test_sentence_transformer_integration(self, mock_transformer_class):
        """Test SentenceTransformer integration"""
        # Mock model
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_transformer_class.return_value = mock_model
        
        # Create embedding client
        client = ServerlessEmbeddingClient("sentence-transformers/all-MiniLM-L6-v2")
        
        # Test single embedding
        text = "How do programs build confidence?"
        embedding = client.encode_single(text)
        
        self.assertEqual(embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model.encode.assert_called_with([text])
        
        # Test batch embedding
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_model.encode.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        
        embeddings = client.encode_batch(texts, use_cache=False)
        
        self.assertEqual(len(embeddings), 3)
        self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])
        self.assertEqual(embeddings[2], [0.7, 0.8, 0.9])
        
        # Test caching behavior
        stats = client.get_stats()
        self.assertGreater(stats['cache_hit_rate'], 0)  # Should have some cache hits
    
    @patch('embeddings.SentenceTransformer')
    def test_embedding_performance_optimization(self, mock_transformer_class):
        """Test embedding performance optimizations"""
        # Mock model with timing simulation
        mock_model = Mock()
        
        def mock_encode(texts):
            # Simulate processing time
            time.sleep(0.01 * len(texts))
            return [[0.1, 0.2, 0.3] for _ in texts]
        
        mock_model.encode.side_effect = mock_encode
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient("sentence-transformers/all-MiniLM-L6-v2")
        
        # Test batch processing is more efficient than individual calls
        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        
        # Batch processing
        start_time = time.time()
        batch_embeddings = client.encode_batch(texts, use_cache=False)
        batch_time = time.time() - start_time
        
        # Individual processing
        start_time = time.time()
        individual_embeddings = []
        for text in texts:
            embedding = client.encode_single(text, use_cache=False)
            individual_embeddings.append(embedding)
        individual_time = time.time() - start_time
        
        # Batch should be faster (or at least not significantly slower)
        self.assertLessEqual(batch_time, individual_time * 1.5)
        
        # Results should be the same
        self.assertEqual(len(batch_embeddings), len(individual_embeddings))


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_complete_rag_pipeline(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test complete RAG pipeline integration"""
        # Mock all components
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_transformer_class.return_value = mock_embeddings
        
        mock_vector_client = Mock()
        mock_search_results = [
            {
                "text": "Programs help build confidence through structured activities and peer support.",
                "organization": "YCUK",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "How do programs help?"
            }
        ]
        mock_vector_client.search.return_value = mock_search_results
        mock_vector_client.health_check.return_value = True
        mock_factory.create_client.return_value = mock_vector_client
        
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Based on survey responses from YCUK participants aged 16-18, programs build confidence through structured activities, peer support, and skill development opportunities."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        # Create RAG engine
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index",
            "vector_store_type": "pinecone",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_tokens": 1000,
            "max_results": 5
        }
        
        engine = ServerlessRAGEngine(config)
        
        # Test complete query processing
        query = "How do programs build confidence in young people?"
        result = engine.process_query(query)
        
        # Verify complete pipeline execution
        self.assertEqual(result['question'], query)
        self.assertIn('confidence', result['answer'].lower())
        self.assertEqual(result['evidence_count'], 1)
        self.assertIn('YCUK', result['organizations'])
        self.assertIn('16-18', result['age_groups'])
        self.assertGreater(result['processing_time'], 0)
        
        # Verify all components were called
        mock_embeddings.encode.assert_called_once()
        mock_vector_client.search.assert_called_once()
        mock_llm.invoke.assert_called_once()
    
    @patch('conversation.ServerlessRAGEngine')
    def test_conversational_rag_integration(self, mock_rag_class):
        """Test conversational RAG integration"""
        # Mock RAG engine
        mock_engine = Mock()
        mock_engine.process_query.return_value = {
            'question': 'test',
            'answer': 'Test response',
            'source_documents': [{'text': 'Test doc', 'organization': 'Test Org'}],
            'evidence_count': 1,
            'organizations': ['Test Org'],
            'age_groups': ['16-18'],
            'genders': ['Female'],
            'processing_time': 1.0
        }
        mock_rag_class.return_value = mock_engine
        
        # Create conversational adapter
        adapter = ConversationalRAGAdapter(mock_engine)
        
        # Test multi-turn conversation
        session_id = "test_session"
        
        # First turn
        response1 = adapter.chat("How do programs help?", session_id)
        self.assertEqual(response1['turn_number'], 1)
        self.assertFalse(response1['conversation_context_used'])
        
        # Second turn (should use context)
        response2 = adapter.chat("What about confidence building?", session_id, include_context=True)
        self.assertEqual(response2['turn_number'], 2)
        self.assertTrue(response2['conversation_context_used'])
        
        # Verify conversation history
        history = adapter.get_conversation_history(session_id)
        self.assertEqual(history['total_turns'], 2)
        self.assertEqual(len(history['turns']), 2)
    
    def test_error_propagation_through_pipeline(self):
        """Test error propagation through the complete pipeline"""
        # Test with missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception):
                engine = ServerlessRAGEngine()
                engine.process_query("test query")
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_performance_under_load(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test system performance under simulated load"""
        # Mock components with realistic delays
        mock_embeddings = Mock()
        
        def mock_encode(texts):
            time.sleep(0.1)  # Simulate embedding generation time
            return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in texts]
        
        mock_embeddings.encode.side_effect = mock_encode
        mock_transformer_class.return_value = mock_embeddings
        
        mock_vector_client = Mock()
        
        def mock_search(query_embedding, top_k, filters=None):
            time.sleep(0.05)  # Simulate vector search time
            return [
                {
                    "text": f"Result for query",
                    "organization": "Test Org",
                    "age_group": "16-18",
                    "gender": "Female"
                }
            ]
        
        mock_vector_client.search.side_effect = mock_search
        mock_factory.create_client.return_value = mock_vector_client
        
        mock_llm = Mock()
        
        def mock_invoke(prompt):
            time.sleep(0.2)  # Simulate LLM response time
            mock_response = Mock()
            mock_response.content = "Test response"
            return mock_response
        
        mock_llm.invoke.side_effect = mock_invoke
        mock_llm_class.return_value = mock_llm
        
        # Create engine
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index",
            "vector_store_type": "pinecone"
        }
        
        engine = ServerlessRAGEngine(config)
        
        # Test multiple queries
        queries = [
            "How do programs build confidence?",
            "What about social skills?",
            "Are there creative activities?",
            "How do you measure success?",
            "What challenges do participants face?"
        ]
        
        start_time = time.time()
        results = []
        
        for query in queries:
            result = engine.process_query(query)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # All queries should succeed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIn('answer', result)
            self.assertGreater(result['processing_time'], 0)
        
        # Average processing time should be reasonable
        avg_time = total_time / len(queries)
        self.assertLess(avg_time, 2.0)  # Should average under 2 seconds per query


if __name__ == '__main__':
    unittest.main()