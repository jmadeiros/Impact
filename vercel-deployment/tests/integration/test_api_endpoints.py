"""
Integration tests for API endpoints
Tests end-to-end API functionality with mocked external services
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, patch
import json
import os
import sys
import time
from typing import Dict, Any

# Add lib and api directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))


class TestSearchAPIIntegration(unittest.TestCase):
    """Integration tests for search API endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_request = {
            "query": "How do programs build confidence in young people?",
            "max_results": 5,
            "filters": {
                "age_group": ["16-18"],
                "organization": ["YCUK"]
            }
        }
        
        self.mock_search_results = [
            {
                "id": "doc1",
                "score": 0.95,
                "text": "Programs help build confidence through structured activities and peer support.",
                "organization": "YCUK",
                "age_group": "16-18",
                "gender": "Female",
                "question_text": "How has this program impacted your confidence?"
            }
        ]
        
        self.mock_rag_response = {
            'question': self.test_request["query"],
            'answer': 'Based on survey responses from YCUK participants aged 16-18, programs build confidence through structured activities, peer support, and skill development opportunities.',
            'source_documents': self.mock_search_results,
            'evidence_count': 1,
            'organizations': ['YCUK'],
            'age_groups': ['16-18'],
            'genders': ['Female'],
            'system_type': 'serverless_rag',
            'processing_time': 1.5
        }
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_search_endpoint_success(self, mock_rag_class):
        """Test successful search API request"""
        # Mock RAG engine
        mock_engine = Mock()
        mock_engine.process_query.return_value = self.mock_rag_response
        mock_rag_class.return_value = mock_engine
        
        # Import and test search endpoint
        try:
            from search import handler
            
            # Create mock event
            event = {
                'httpMethod': 'POST',
                'body': json.dumps(self.test_request),
                'headers': {'Content-Type': 'application/json'}
            }
            
            # Call handler
            response = handler(event, {})
            
            # Verify response structure
            self.assertEqual(response['statusCode'], 200)
            
            body = json.loads(response['body'])
            self.assertTrue(body['success'])
            self.assertEqual(body['query'], self.test_request["query"])
            self.assertEqual(body['answer'], self.mock_rag_response['answer'])
            self.assertEqual(body['evidence_count'], 1)
            self.assertIn('processing_time', body)
            self.assertIn('timestamp', body)
            
            # Verify RAG engine was called correctly
            mock_engine.process_query.assert_called_once_with(
                self.test_request["query"],
                filters=self.test_request["filters"]
            )
            
        except ImportError:
            self.skipTest("Search API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_search_endpoint_validation_error(self, mock_rag_class):
        """Test search API with validation errors"""
        try:
            from search import handler
            
            # Test missing query
            event = {
                'httpMethod': 'POST',
                'body': json.dumps({"max_results": 5}),
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 400)
            body = json.loads(response['body'])
            self.assertFalse(body['success'])
            self.assertIn('error', body)
            self.assertEqual(body['error']['type'], 'validation')
            
        except ImportError:
            self.skipTest("Search API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_search_endpoint_rag_error(self, mock_rag_class):
        """Test search API with RAG engine error"""
        # Mock RAG engine to raise exception
        mock_engine = Mock()
        mock_engine.process_query.side_effect = Exception("Vector store connection failed")
        mock_rag_class.return_value = mock_engine
        
        try:
            from search import handler
            
            event = {
                'httpMethod': 'POST',
                'body': json.dumps(self.test_request),
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 500)
            body = json.loads(response['body'])
            self.assertFalse(body['success'])
            self.assertIn('error', body)
            self.assertEqual(body['error']['type'], 'external_service')
            
        except ImportError:
            self.skipTest("Search API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    def test_search_endpoint_method_not_allowed(self):
        """Test search API with wrong HTTP method"""
        try:
            from search import handler
            
            event = {
                'httpMethod': 'GET',
                'body': None,
                'headers': {}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 405)
            body = json.loads(response['body'])
            self.assertFalse(body['success'])
            self.assertIn('error', body)
            
        except ImportError:
            self.skipTest("Search API module not available")


class TestChatAPIIntegration(unittest.TestCase):
    """Integration tests for chat API endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_request = {
            "message": "How do programs build confidence?",
            "session_id": "test_session_123",
            "include_context": True
        }
        
        self.mock_chat_response = {
            'question': self.test_request["message"],
            'answer': 'Programs build confidence through structured activities and peer support.',
            'source_documents': [{'text': 'Test doc', 'organization': 'YCUK'}],
            'evidence_count': 1,
            'organizations': ['YCUK'],
            'age_groups': ['16-18'],
            'genders': ['Female'],
            'session_id': self.test_request["session_id"],
            'turn_number': 1,
            'conversation_context_used': False,
            'total_processing_time': 1.8
        }
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('conversation.ConversationalRAGAdapter')
    def test_chat_endpoint_success(self, mock_adapter_class):
        """Test successful chat API request"""
        # Mock conversational adapter
        mock_adapter = Mock()
        mock_adapter.chat.return_value = self.mock_chat_response
        mock_adapter_class.return_value = mock_adapter
        
        try:
            from chat import handler
            
            event = {
                'httpMethod': 'POST',
                'body': json.dumps(self.test_request),
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            # Verify response structure
            self.assertEqual(response['statusCode'], 200)
            
            body = json.loads(response['body'])
            self.assertTrue(body['success'])
            self.assertEqual(body['message'], self.mock_chat_response['answer'])
            self.assertEqual(body['session_id'], self.test_request["session_id"])
            self.assertEqual(body['turn_number'], 1)
            self.assertIn('timestamp', body)
            
            # Verify adapter was called correctly
            mock_adapter.chat.assert_called_once_with(
                message=self.test_request["message"],
                session_id=self.test_request["session_id"],
                include_context=self.test_request["include_context"]
            )
            
        except ImportError:
            self.skipTest("Chat API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('conversation.ConversationalRAGAdapter')
    def test_chat_endpoint_default_session(self, mock_adapter_class):
        """Test chat API with default session ID"""
        mock_adapter = Mock()
        mock_adapter.chat.return_value = self.mock_chat_response
        mock_adapter_class.return_value = mock_adapter
        
        try:
            from chat import handler
            
            # Request without session_id
            request = {
                "message": "How do programs help?",
                "include_context": False
            }
            
            event = {
                'httpMethod': 'POST',
                'body': json.dumps(request),
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 200)
            
            # Should use default session ID
            mock_adapter.chat.assert_called_once_with(
                message=request["message"],
                session_id="default",
                include_context=False
            )
            
        except ImportError:
            self.skipTest("Chat API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    def test_chat_endpoint_validation_error(self):
        """Test chat API with validation errors"""
        try:
            from chat import handler
            
            # Test missing message
            event = {
                'httpMethod': 'POST',
                'body': json.dumps({"session_id": "test"}),
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 400)
            body = json.loads(response['body'])
            self.assertFalse(body['success'])
            self.assertIn('error', body)
            
        except ImportError:
            self.skipTest("Chat API module not available")


class TestHealthAPIIntegration(unittest.TestCase):
    """Integration tests for health API endpoint"""
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_health_endpoint_basic(self, mock_rag_class):
        """Test basic health check"""
        # Mock healthy RAG engine
        mock_engine = Mock()
        mock_engine.health_check.return_value = {
            'status': 'healthy',
            'components': {
                'vector_store': 'healthy',
                'llm': 'healthy',
                'embeddings': 'healthy'
            },
            'check_time': 0.234
        }
        mock_rag_class.return_value = mock_engine
        
        try:
            from health import handler
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': None,
                'headers': {}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 200)
            
            body = json.loads(response['body'])
            self.assertEqual(body['status'], 'healthy')
            self.assertIn('timestamp', body)
            self.assertIn('service', body)
            self.assertIn('version', body)
            self.assertIn('response_time', body)
            
        except ImportError:
            self.skipTest("Health API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_health_endpoint_detailed(self, mock_rag_class):
        """Test detailed health check"""
        # Mock detailed health response
        mock_engine = Mock()
        mock_engine.health_check.return_value = {
            'status': 'healthy',
            'components': {
                'vector_store': 'healthy',
                'llm': 'healthy',
                'embeddings': 'healthy'
            },
            'config': {
                'vector_store_type': 'pinecone',
                'llm_model': 'gemini-1.5-flash'
            },
            'check_time': 0.456
        }
        
        mock_engine.get_stats.return_value = {
            'system_type': 'serverless_rag',
            'vector_store': {
                'total_vectors': 1000,
                'vector_store_type': 'pinecone'
            }
        }
        
        mock_rag_class.return_value = mock_engine
        
        try:
            from health import handler
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {'detailed': 'true'},
                'headers': {}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 200)
            
            body = json.loads(response['body'])
            self.assertEqual(body['status'], 'healthy')
            self.assertIn('components', body)
            self.assertIn('environment', body)
            self.assertIn('performance', body)
            self.assertIn('system', body)
            
        except ImportError:
            self.skipTest("Health API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_health_endpoint_unhealthy(self, mock_rag_class):
        """Test health check when system is unhealthy"""
        # Mock unhealthy RAG engine
        mock_engine = Mock()
        mock_engine.health_check.return_value = {
            'status': 'unhealthy',
            'components': {
                'vector_store': 'unhealthy',
                'llm': 'healthy',
                'embeddings': 'healthy'
            },
            'error': 'Vector store connection failed',
            'check_time': 0.123
        }
        mock_rag_class.return_value = mock_engine
        
        try:
            from health import handler
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': None,
                'headers': {}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 503)  # Service Unavailable
            
            body = json.loads(response['body'])
            self.assertEqual(body['status'], 'unhealthy')
            
        except ImportError:
            self.skipTest("Health API module not available")


class TestStatsAPIIntegration(unittest.TestCase):
    """Integration tests for stats API endpoint"""
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_stats_endpoint_success(self, mock_rag_class):
        """Test successful stats API request"""
        # Mock stats response
        mock_engine = Mock()
        mock_engine.get_stats.return_value = {
            'system_type': 'serverless_rag',
            'vector_store': {
                'total_vectors': 1000,
                'dimension': 384,
                'vector_store_type': 'pinecone',
                'index_name': 'test_index'
            },
            'config': {
                'llm_model': 'gemini-1.5-flash',
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
                'max_results': 5
            }
        }
        mock_rag_class.return_value = mock_engine
        
        try:
            from stats import handler
            
            event = {
                'httpMethod': 'GET',
                'headers': {}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 200)
            
            body = json.loads(response['body'])
            self.assertEqual(body['system_type'], 'serverless_rag')
            self.assertIn('vector_store', body)
            self.assertIn('config', body)
            self.assertIn('timestamp', body)
            
            # Verify vector store stats
            vector_stats = body['vector_store']
            self.assertEqual(vector_stats['total_vectors'], 1000)
            self.assertEqual(vector_stats['vector_store_type'], 'pinecone')
            
        except ImportError:
            self.skipTest("Stats API module not available")


class TestAPIErrorHandling(unittest.TestCase):
    """Integration tests for API error handling"""
    
    def test_invalid_json_body(self):
        """Test API handling of invalid JSON in request body"""
        try:
            from search import handler
            
            event = {
                'httpMethod': 'POST',
                'body': '{"invalid": json}',  # Invalid JSON
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 400)
            body = json.loads(response['body'])
            self.assertFalse(body['success'])
            self.assertIn('error', body)
            
        except ImportError:
            self.skipTest("Search API module not available")
    
    def test_missing_content_type(self):
        """Test API handling of missing content type"""
        try:
            from search import handler
            
            event = {
                'httpMethod': 'POST',
                'body': json.dumps({"query": "test"}),
                'headers': {}  # Missing Content-Type
            }
            
            response = handler(event, {})
            
            # Should still work, but might have different behavior
            self.assertIn(response['statusCode'], [200, 400])
            
        except ImportError:
            self.skipTest("Search API module not available")
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    def test_missing_environment_variables(self):
        """Test API handling when environment variables are missing"""
        try:
            from search import handler
            
            event = {
                'httpMethod': 'POST',
                'body': json.dumps({"query": "test"}),
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = handler(event, {})
            
            self.assertEqual(response['statusCode'], 500)
            body = json.loads(response['body'])
            self.assertFalse(body['success'])
            self.assertIn('error', body)
            
        except ImportError:
            self.skipTest("Search API module not available")


class TestAPIPerformance(unittest.TestCase):
    """Integration tests for API performance characteristics"""
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_search_response_time(self, mock_rag_class):
        """Test that search API responds within reasonable time"""
        # Mock fast RAG engine
        mock_engine = Mock()
        mock_engine.process_query.return_value = {
            'question': 'test',
            'answer': 'test answer',
            'source_documents': [],
            'evidence_count': 0,
            'organizations': [],
            'age_groups': [],
            'genders': [],
            'processing_time': 0.5
        }
        mock_rag_class.return_value = mock_engine
        
        try:
            from search import handler
            
            event = {
                'httpMethod': 'POST',
                'body': json.dumps({"query": "test query"}),
                'headers': {'Content-Type': 'application/json'}
            }
            
            start_time = time.time()
            response = handler(event, {})
            end_time = time.time()
            
            # API should respond quickly (under 5 seconds for mocked components)
            response_time = end_time - start_time
            self.assertLess(response_time, 5.0)
            
            # Response should include timing information
            body = json.loads(response['body'])
            self.assertIn('processing_time', body)
            
        except ImportError:
            self.skipTest("Search API module not available")
    
    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_key",
        "PINECONE_API_KEY": "test_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index"
    })
    @patch('rag_engine.ServerlessRAGEngine')
    def test_concurrent_requests_simulation(self, mock_rag_class):
        """Test API behavior under simulated concurrent load"""
        # Mock RAG engine with slight delay
        mock_engine = Mock()
        
        def mock_process_query(query, filters=None):
            time.sleep(0.1)  # Simulate processing time
            return {
                'question': query,
                'answer': f'Answer for: {query}',
                'source_documents': [],
                'evidence_count': 0,
                'organizations': [],
                'age_groups': [],
                'genders': [],
                'processing_time': 0.1
            }
        
        mock_engine.process_query.side_effect = mock_process_query
        mock_rag_class.return_value = mock_engine
        
        try:
            from search import handler
            
            # Simulate multiple requests
            requests = []
            for i in range(5):
                event = {
                    'httpMethod': 'POST',
                    'body': json.dumps({"query": f"test query {i}"}),
                    'headers': {'Content-Type': 'application/json'}
                }
                requests.append(event)
            
            # Process requests sequentially (simulating serverless behavior)
            responses = []
            start_time = time.time()
            
            for event in requests:
                response = handler(event, {})
                responses.append(response)
            
            end_time = time.time()
            
            # All requests should succeed
            for response in responses:
                self.assertEqual(response['statusCode'], 200)
            
            # Total time should be reasonable
            total_time = end_time - start_time
            self.assertLess(total_time, 10.0)  # Should complete within 10 seconds
            
        except ImportError:
            self.skipTest("Search API module not available")


if __name__ == '__main__':
    unittest.main()