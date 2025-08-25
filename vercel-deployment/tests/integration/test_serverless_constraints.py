"""
Integration tests for serverless constraints and optimizations
Tests cold start performance, memory usage, timeout handling, and stateless operation
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import time
import threading
from typing import Dict, Any, List

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from rag_engine import ServerlessRAGEngine
from embeddings import ServerlessEmbeddingClient
from conversation import ServerlessConversationManager


class TestColdStartPerformance(unittest.TestCase):
    """Test cold start performance and initialization optimizations"""
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_lazy_loading_initialization(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test that components are lazy-loaded for fast cold starts"""
        # Mock components
        mock_llm = Mock()
        mock_embeddings = Mock()
        mock_vector_client = Mock()
        
        mock_llm_class.return_value = mock_llm
        mock_transformer_class.return_value = mock_embeddings
        mock_factory.create_client.return_value = mock_vector_client
        
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index"
        }
        
        # Measure initialization time
        start_time = time.time()
        engine = ServerlessRAGEngine(config)
        init_time = time.time() - start_time
        
        # Initialization should be very fast (no heavy loading)
        self.assertLess(init_time, 0.1)  # Should initialize in under 100ms
        
        # Components should not be initialized yet
        self.assertIsNone(engine._llm)
        self.assertIsNone(engine._embeddings)
        self.assertIsNone(engine._vector_client)
        
        # Components should not have been called during initialization
        mock_llm_class.assert_not_called()
        mock_transformer_class.assert_not_called()
        mock_factory.create_client.assert_not_called()
        
        # First access should trigger initialization
        start_time = time.time()
        llm = engine.llm
        llm_init_time = time.time() - start_time
        
        # Component initialization should be reasonably fast
        self.assertLess(llm_init_time, 2.0)  # Should initialize in under 2 seconds
        mock_llm_class.assert_called_once()
    
    @patch('embeddings.SentenceTransformer')
    def test_embedding_client_cold_start(self, mock_transformer_class):
        """Test embedding client cold start performance"""
        mock_model = Mock()
        mock_transformer_class.return_value = mock_model
        
        # Measure initialization time
        start_time = time.time()
        client = ServerlessEmbeddingClient("sentence-transformers/all-MiniLM-L6-v2")
        init_time = time.time() - start_time
        
        # Should initialize quickly without loading model
        self.assertLess(init_time, 0.1)
        self.assertIsNone(client._model)
        
        # First use should load model
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        
        start_time = time.time()
        embedding = client.encode_single("test text")
        first_use_time = time.time() - start_time
        
        # First use includes model loading time
        self.assertLess(first_use_time, 3.0)  # Should load and encode in under 3 seconds
        mock_transformer_class.assert_called_once()
    
    def test_conversation_manager_cold_start(self):
        """Test conversation manager cold start performance"""
        start_time = time.time()
        manager = ServerlessConversationManager()
        init_time = time.time() - start_time
        
        # Should initialize instantly
        self.assertLess(init_time, 0.01)
        self.assertEqual(len(manager._sessions), 0)
        
        # Creating sessions should be fast
        start_time = time.time()
        session = manager.create_session("test_session")
        session_time = time.time() - start_time
        
        self.assertLess(session_time, 0.01)
        self.assertIsNotNone(session)


class TestMemoryOptimization(unittest.TestCase):
    """Test memory usage optimization for serverless constraints"""
    
    @patch('embeddings.SentenceTransformer')
    def test_embedding_cache_memory_management(self, mock_transformer_class):
        """Test embedding cache memory management"""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient("sentence-transformers/all-MiniLM-L6-v2")
        
        # Generate many embeddings to test cache behavior
        texts = [f"Test text {i}" for i in range(1000)]
        
        # Process in batches to simulate real usage
        for i in range(0, len(texts), 50):
            batch = texts[i:i+50]
            client.encode_batch(batch, use_cache=True)
        
        # Cache should not grow indefinitely
        cache_size = len(client._cache)
        self.assertLess(cache_size, 200)  # Should limit cache size
        
        # Clear cache to free memory
        client.clear_cache()
        self.assertEqual(len(client._cache), 0)
    
    def test_conversation_session_memory_limits(self):
        """Test conversation session memory limits"""
        manager = ServerlessConversationManager(max_turns_per_session=5)
        session_id = "test_session"
        
        # Add many turns to test memory management
        for i in range(10):
            manager.add_turn(
                session_id=session_id,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                evidence_count=1,
                organizations=["Test Org"],
                age_groups=["16-18"],
                processing_time=1.0
            )
        
        session = manager.get_session(session_id)
        
        # Should limit number of turns to prevent memory growth
        self.assertEqual(len(session.turns), 5)
        
        # Should keep only the most recent turns
        self.assertEqual(session.turns[0].user_message, "Message 5")
        self.assertEqual(session.turns[-1].user_message, "Message 9")
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_stateless_operation(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test stateless operation without persistent state"""
        # Mock components
        mock_llm = Mock()
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_vector_client = Mock()
        mock_vector_client.search.return_value = []
        
        mock_llm_class.return_value = mock_llm
        mock_transformer_class.return_value = mock_embeddings
        mock_factory.create_client.return_value = mock_vector_client
        
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index"
        }
        
        # Create multiple engine instances (simulating different function invocations)
        engines = []
        for i in range(3):
            engine = ServerlessRAGEngine(config)
            engines.append(engine)
        
        # Each engine should be independent
        for i, engine in enumerate(engines):
            # Should not share state between instances
            self.assertIsNone(engine._llm)
            self.assertIsNone(engine._embeddings)
            self.assertIsNone(engine._vector_client)
            
            # Each should initialize independently
            result = engine.process_query(f"Query {i}")
            self.assertIn('answer', result)


class TestTimeoutHandling(unittest.TestCase):
    """Test timeout handling and performance constraints"""
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_query_processing_timeout(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test query processing within timeout constraints"""
        # Mock components with realistic delays
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        mock_vector_client = Mock()
        mock_vector_client.search.return_value = [
            {
                "text": "Test document",
                "organization": "Test Org",
                "age_group": "16-18",
                "gender": "Female"
            }
        ]
        mock_factory.create_client.return_value = mock_vector_client
        
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index",
            "timeout_seconds": 25
        }
        
        engine = ServerlessRAGEngine(config)
        
        # Test query processing time
        start_time = time.time()
        result = engine.process_query("How do programs build confidence?")
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time for serverless
        self.assertLess(processing_time, 10.0)  # Should complete in under 10 seconds
        self.assertIn('processing_time', result)
        self.assertGreater(result['processing_time'], 0)
    
    @patch('embeddings.SentenceTransformer')
    def test_embedding_generation_timeout(self, mock_transformer_class):
        """Test embedding generation timeout handling"""
        # Mock model with delay
        mock_model = Mock()
        
        def slow_encode(texts):
            time.sleep(0.1)  # Simulate processing time
            return [[0.1, 0.2, 0.3] for _ in texts]
        
        mock_model.encode.side_effect = slow_encode
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient("sentence-transformers/all-MiniLM-L6-v2")
        
        # Test batch processing with timeout considerations
        texts = [f"Text {i}" for i in range(100)]
        
        start_time = time.time()
        embeddings = client.encode_batch(texts, batch_size=10)
        processing_time = time.time() - start_time
        
        # Should complete in reasonable time
        self.assertLess(processing_time, 5.0)
        self.assertEqual(len(embeddings), 100)
    
    def test_conversation_session_timeout(self):
        """Test conversation session timeout handling"""
        manager = ServerlessConversationManager(session_timeout_hours=0.001)  # Very short timeout
        
        # Create session
        session = manager.create_session("test_session")
        self.assertIsNotNone(session)
        
        # Wait for timeout
        time.sleep(0.1)
        
        # Session should be expired and removed
        expired_session = manager.get_session("test_session")
        self.assertIsNone(expired_session)


class TestConcurrencyAndStatelessness(unittest.TestCase):
    """Test concurrent access and stateless behavior"""
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_concurrent_query_processing(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test concurrent query processing (simulating multiple serverless invocations)"""
        # Mock components
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        mock_vector_client = Mock()
        mock_vector_client.search.return_value = []
        mock_factory.create_client.return_value = mock_vector_client
        
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index"
        }
        
        # Simulate concurrent processing
        results = []
        errors = []
        
        def process_query(query_id):
            try:
                engine = ServerlessRAGEngine(config)
                result = engine.process_query(f"Query {query_id}")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads (simulating concurrent serverless invocations)
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_query, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All queries should succeed
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # Each result should be independent
        for i, result in enumerate(results):
            self.assertIn('answer', result)
            self.assertGreater(result['processing_time'], 0)
    
    def test_conversation_session_isolation(self):
        """Test conversation session isolation between different managers"""
        # Create multiple managers (simulating different function invocations)
        managers = [ServerlessConversationManager() for _ in range(3)]
        
        # Each should be independent
        for i, manager in enumerate(managers):
            session = manager.create_session(f"session_{i}")
            self.assertEqual(len(manager._sessions), 1)
            self.assertIn(f"session_{i}", manager._sessions)
        
        # Sessions should not be shared between managers
        for i, manager in enumerate(managers):
            for j in range(3):
                if i == j:
                    self.assertIsNotNone(manager.get_session(f"session_{j}"))
                else:
                    self.assertIsNone(manager.get_session(f"session_{j}"))


class TestResourceConstraints(unittest.TestCase):
    """Test behavior under serverless resource constraints"""
    
    @patch('embeddings.SentenceTransformer')
    def test_large_batch_processing(self, mock_transformer_class):
        """Test processing large batches within memory constraints"""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3] for _ in range(100)]
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient("sentence-transformers/all-MiniLM-L6-v2")
        
        # Test large batch processing
        large_texts = [f"Text {i}" for i in range(1000)]
        
        start_time = time.time()
        embeddings = client.encode_batch(large_texts, batch_size=50)
        processing_time = time.time() - start_time
        
        # Should handle large batches efficiently
        self.assertEqual(len(embeddings), 1000)
        self.assertLess(processing_time, 10.0)  # Should complete in reasonable time
        
        # Should use batching to manage memory
        self.assertGreater(mock_model.encode.call_count, 1)  # Should be called multiple times
    
    def test_memory_efficient_document_processing(self):
        """Test memory-efficient document processing"""
        # Simulate processing many documents
        documents = []
        for i in range(100):
            doc = {
                "id": f"doc_{i}",
                "text": f"This is document {i} with some content that takes up memory.",
                "embedding": [0.1 * j for j in range(384)],  # Large embedding
                "metadata": {
                    "organization": f"Org_{i % 10}",
                    "age_group": "16-18",
                    "created_at": "2024-01-01T10:00:00Z"
                }
            }
            documents.append(doc)
        
        # Process documents in batches to manage memory
        batch_size = 10
        processed_count = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Simulate processing batch
            for doc in batch:
                # Process document (simulate some work)
                processed_count += 1
            
            # Clear batch from memory
            del batch
        
        self.assertEqual(processed_count, 100)
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('rag_engine.SentenceTransformer')
    @patch('rag_engine.ChatGoogleGenerativeAI')
    def test_error_recovery_and_graceful_degradation(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test error recovery and graceful degradation under constraints"""
        # Mock components with intermittent failures
        mock_embeddings = Mock()
        mock_embeddings.encode.side_effect = [
            [[0.1, 0.2, 0.3]],  # Success
            Exception("Temporary failure"),  # Failure
            [[0.4, 0.5, 0.6]]   # Recovery
        ]
        mock_transformer_class.return_value = mock_embeddings
        
        mock_vector_client = Mock()
        mock_vector_client.search.return_value = []
        mock_factory.create_client.return_value = mock_vector_client
        
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Fallback response"
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        config = {
            "google_api_key": "test_key",
            "pinecone_api_key": "test_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index"
        }
        
        engine = ServerlessRAGEngine(config)
        
        # First query should succeed
        result1 = engine.process_query("Query 1")
        self.assertIn('answer', result1)
        
        # Second query should handle failure gracefully
        result2 = engine.process_query("Query 2")
        # Should return error response or fallback
        self.assertIn('answer', result2)
        
        # Third query should recover
        result3 = engine.process_query("Query 3")
        self.assertIn('answer', result3)


if __name__ == '__main__':
    unittest.main()