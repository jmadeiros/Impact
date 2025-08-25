"""
Unit tests for ServerlessRAGEngine
Tests core RAG functionality, error handling, and serverless optimizations
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import time
from typing import List, Dict, Any

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from rag_engine import ServerlessRAGEngine, create_rag_engine, validate_environment


class TestServerlessRAGEngine(unittest.TestCase):
    """Test cases for ServerlessRAGEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "google_api_key": "test_google_key",
            "pinecone_api_key": "test_pinecone_key",
            "pinecone_environment": "test_env",
            "pinecone_index_name": "test_index",
            "pinecone_namespace": "test",
            "supabase_url": "test_url",
            "supabase_key": "test_key",
            "vector_store_type": "pinecone",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_tokens": 1000,
            "max_results": 5,
            "timeout_seconds": 25
        }
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            "GOOGLE_API_KEY": "test_google_key",
            "PINECONE_API_KEY": "test_pinecone_key",
            "PINECONE_ENVIRONMENT": "test_env",
            "PINECONE_INDEX_NAME": "test_index"
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    def test_initialization_with_config(self):
        """Test RAG engine initialization with provided config"""
        engine = ServerlessRAGEngine(self.test_config)
        
        self.assertEqual(engine.config["google_api_key"], "test_google_key")
        self.assertEqual(engine.config["vector_store_type"], "pinecone")
        self.assertEqual(engine.config["max_results"], 5)
        self.assertIsNone(engine._llm)  # Should be lazy-loaded
        self.assertIsNone(engine._embeddings)  # Should be lazy-loaded
        self.assertIsNone(engine._vector_client)  # Should be lazy-loaded
    
    def test_initialization_from_env(self):
        """Test RAG engine initialization from environment variables"""
        engine = ServerlessRAGEngine()
        
        self.assertEqual(engine.config["google_api_key"], "test_google_key")
        self.assertEqual(engine.config["pinecone_api_key"], "test_pinecone_key")
        self.assertEqual(engine.config["vector_store_type"], "pinecone")
    
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_llm_initialization(self, mock_llm_class):
        """Test LLM lazy initialization"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Access LLM property to trigger initialization
        llm = engine.llm
        
        self.assertEqual(llm, mock_llm)
        mock_llm_class.assert_called_once_with(
            model="gemini-1.5-flash",
            google_api_key="test_google_key",
            temperature=0.1,
            max_tokens=1000
        )
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_embeddings_initialization(self, mock_transformer_class):
        """Test embeddings lazy initialization"""
        mock_embeddings = Mock()
        mock_transformer_class.return_value = mock_embeddings
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Access embeddings property to trigger initialization
        embeddings = engine.embeddings
        
        self.assertEqual(embeddings, mock_embeddings)
        mock_transformer_class.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")
        mock_embeddings.eval.assert_called_once()
    
    @patch('rag_engine.VectorStoreFactory')
    def test_vector_client_initialization(self, mock_factory):
        """Test vector client lazy initialization"""
        mock_client = Mock()
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Access vector_client property to trigger initialization
        client = engine.vector_client
        
        self.assertEqual(client, mock_client)
        mock_factory.create_client.assert_called_once_with(self.test_config)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embedding_with_caching(self, mock_transformer_class):
        """Test embedding generation with LRU caching"""
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # First call should generate embedding
        embedding1 = engine._generate_embedding("test text")
        self.assertEqual(embedding1, [0.1, 0.2, 0.3])
        
        # Second call with same text should use cache
        embedding2 = engine._generate_embedding("test text")
        self.assertEqual(embedding2, [0.1, 0.2, 0.3])
        
        # Should only call encode once due to caching
        mock_embeddings.encode.assert_called_once_with(["test text"])
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('sentence_transformers.SentenceTransformer')
    def test_search_similar_documents(self, mock_transformer_class, mock_factory):
        """Test document similarity search"""
        # Mock embeddings
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        # Mock vector client
        mock_client = Mock()
        mock_search_results = [
            {
                "id": "doc1",
                "score": 0.9,
                "text": "Test document 1",
                "organization": "Test Org",
                "age_group": "16-18",
                "gender": "Male"
            }
        ]
        mock_client.search.return_value = mock_search_results
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Test search
        results = engine.search_similar_documents("test query", max_results=3)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "Test document 1")
        
        # Verify vector client was called correctly
        mock_client.search.assert_called_once_with(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=3,
            filters=None
        )
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('sentence_transformers.SentenceTransformer')
    def test_search_with_filters(self, mock_transformer_class, mock_factory):
        """Test document search with filters"""
        # Mock embeddings
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        # Mock vector client
        mock_client = Mock()
        mock_client.search.return_value = []
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Test search with filters
        filters = {"age_group": ["16-18"], "organization": ["Test Org"]}
        engine.search_similar_documents("test query", filters=filters)
        
        # Verify filters were passed correctly
        mock_client.search.assert_called_once_with(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,  # default max_results
            filters=filters
        )
    
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_generate_response(self, mock_llm_class):
        """Test AI response generation"""
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "This is a test response based on the survey data."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Test response generation
        context_docs = [
            {
                "text": "Programs help build confidence",
                "organization": "Test Org",
                "age_group": "16-18",
                "gender": "Male",
                "question_text": "How do programs help?"
            }
        ]
        
        response = engine.generate_response("How do programs build confidence?", context_docs)
        
        self.assertEqual(response, "This is a test response based on the survey data.")
        mock_llm.invoke.assert_called_once()
        
        # Verify prompt contains context
        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIn("Programs help build confidence", call_args)
        self.assertIn("How do programs build confidence?", call_args)
    
    def test_format_context_documents(self):
        """Test context document formatting"""
        engine = ServerlessRAGEngine(self.test_config)
        
        documents = [
            {
                "text": "Programs help build confidence through activities",
                "organization": "YCUK",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "How do programs help you?"
            },
            {
                "text": "I made many friends through the program",
                "organization": "Palace for Life",
                "age_group": "13-15",
                "gender": "Male",
                "question_text": "What did you gain from the program?"
            }
        ]
        
        formatted = engine._format_context_documents(documents)
        
        self.assertIn("Survey Response 1:", formatted)
        self.assertIn("Survey Response 2:", formatted)
        self.assertIn("Organization: YCUK", formatted)
        self.assertIn("Age Group: 16-18", formatted)
        self.assertIn("Programs help build confidence", formatted)
        self.assertIn("I made many friends", formatted)
    
    def test_format_empty_context_documents(self):
        """Test formatting when no documents provided"""
        engine = ServerlessRAGEngine(self.test_config)
        
        formatted = engine._format_context_documents([])
        
        self.assertEqual(formatted, "No relevant survey responses found.")
    
    def test_create_prompt(self):
        """Test prompt creation"""
        engine = ServerlessRAGEngine(self.test_config)
        
        query = "How do programs build confidence?"
        context = "Survey Response 1:\nPrograms help through activities"
        
        prompt = engine._create_prompt(query, context)
        
        self.assertIn("friendly and knowledgeable assistant", prompt)
        self.assertIn("How do programs build confidence?", prompt)
        self.assertIn("Programs help through activities", prompt)
        self.assertIn("conversational response", prompt)
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('sentence_transformers.SentenceTransformer')
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_process_query_success(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test complete query processing pipeline"""
        # Mock all components
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        mock_client = Mock()
        mock_search_results = [
            {
                "text": "Programs build confidence through activities",
                "organization": "YCUK",
                "age_group": "16-18",
                "gender": "Female"
            }
        ]
        mock_client.search.return_value = mock_search_results
        mock_factory.create_client.return_value = mock_client
        
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Based on survey data, programs build confidence through structured activities."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Process query
        result = engine.process_query("How do programs build confidence?")
        
        # Verify response structure
        self.assertIn('question', result)
        self.assertIn('answer', result)
        self.assertIn('source_documents', result)
        self.assertIn('evidence_count', result)
        self.assertIn('organizations', result)
        self.assertIn('age_groups', result)
        self.assertIn('processing_time', result)
        
        # Verify content
        self.assertEqual(result['question'], "How do programs build confidence?")
        self.assertEqual(result['evidence_count'], 1)
        self.assertIn('YCUK', result['organizations'])
        self.assertIn('16-18', result['age_groups'])
        self.assertGreater(result['processing_time'], 0)
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('sentence_transformers.SentenceTransformer')
    def test_process_query_no_results(self, mock_transformer_class, mock_factory):
        """Test query processing when no documents found"""
        # Mock embeddings
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        # Mock vector client returning no results
        mock_client = Mock()
        mock_client.search.return_value = []
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Process query
        result = engine.process_query("Obscure query with no matches")
        
        # Verify no-results response
        self.assertEqual(result['evidence_count'], 0)
        self.assertEqual(len(result['source_documents']), 0)
        self.assertIn("couldn't find any relevant", result['answer'])
    
    @patch('rag_engine.VectorStoreFactory')
    def test_process_query_error_handling(self, mock_factory):
        """Test error handling in query processing"""
        # Mock vector client that raises exception
        mock_client = Mock()
        mock_client.search.side_effect = Exception("Vector store connection failed")
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Process query
        result = engine.process_query("Test query")
        
        # Verify error response
        self.assertIn('error', result)
        self.assertIn("encountered an error", result['answer'])
        self.assertEqual(result['evidence_count'], 0)
    
    @patch('rag_engine.VectorStoreFactory')
    @patch('sentence_transformers.SentenceTransformer')
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_health_check_healthy(self, mock_llm_class, mock_transformer_class, mock_factory):
        """Test health check when all components are healthy"""
        # Mock all components as healthy
        mock_embeddings = Mock()
        mock_embeddings.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer_class.return_value = mock_embeddings
        
        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_factory.create_client.return_value = mock_client
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = "Hello"
        mock_llm_class.return_value = mock_llm
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Run health check
        health = engine.health_check()
        
        # Verify healthy status
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['components']['vector_store'], 'healthy')
        self.assertEqual(health['components']['llm'], 'healthy')
        self.assertEqual(health['components']['embeddings'], 'healthy')
        self.assertIn('config', health)
        self.assertGreater(health['check_time'], 0)
    
    @patch('rag_engine.VectorStoreFactory')
    def test_health_check_unhealthy(self, mock_factory):
        """Test health check when components are unhealthy"""
        # Mock vector client as unhealthy
        mock_client = Mock()
        mock_client.health_check.return_value = False
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Run health check
        health = engine.health_check()
        
        # Verify unhealthy status
        self.assertEqual(health['status'], 'unhealthy')
        self.assertEqual(health['components']['vector_store'], 'unhealthy')
    
    @patch('rag_engine.VectorStoreFactory')
    def test_get_stats(self, mock_factory):
        """Test statistics retrieval"""
        # Mock vector client stats
        mock_client = Mock()
        mock_stats = {
            "total_vectors": 1000,
            "vector_store_type": "pinecone"
        }
        mock_client.get_stats.return_value = mock_stats
        mock_factory.create_client.return_value = mock_client
        
        engine = ServerlessRAGEngine(self.test_config)
        
        # Get stats
        stats = engine.get_stats()
        
        # Verify stats structure
        self.assertEqual(stats['system_type'], 'serverless_rag')
        self.assertEqual(stats['vector_store'], mock_stats)
        self.assertIn('config', stats)
        self.assertEqual(stats['config']['llm_model'], 'gemini-1.5-flash')


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_rag_engine(self):
        """Test RAG engine factory function"""
        config = {"test": "value"}
        engine = create_rag_engine(config)
        
        self.assertIsInstance(engine, ServerlessRAGEngine)
        self.assertEqual(engine.config["test"], "value")
    
    def test_create_rag_engine_no_config(self):
        """Test RAG engine factory without config"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}):
            engine = create_rag_engine()
            self.assertIsInstance(engine, ServerlessRAGEngine)
    
    def test_validate_environment_complete(self):
        """Test environment validation with all variables"""
        with patch.dict(os.environ, {
            "GOOGLE_API_KEY": "test_key",
            "PINECONE_API_KEY": "test_key",
            "PINECONE_ENVIRONMENT": "test_env",
            "PINECONE_INDEX_NAME": "test_index"
        }):
            validation = validate_environment()
            
            self.assertTrue(all(validation.values()))
            self.assertIn("GOOGLE_API_KEY", validation)
            self.assertIn("PINECONE_API_KEY", validation)
    
    def test_validate_environment_missing(self):
        """Test environment validation with missing variables"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}, clear=True):
            validation = validate_environment()
            
            self.assertTrue(validation["GOOGLE_API_KEY"])
            self.assertFalse(validation["PINECONE_API_KEY"])
            self.assertFalse(validation["PINECONE_ENVIRONMENT"])
            self.assertFalse(validation["PINECONE_INDEX_NAME"])


if __name__ == '__main__':
    unittest.main()