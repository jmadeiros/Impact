"""
Test configuration and fixtures for pytest
Provides common test utilities and mock objects
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))


@pytest.fixture
def mock_environment():
    """Fixture providing mock environment variables"""
    env_vars = {
        "GOOGLE_API_KEY": "test_google_key",
        "PINECONE_API_KEY": "test_pinecone_key",
        "PINECONE_ENVIRONMENT": "test_env",
        "PINECONE_INDEX_NAME": "test_index",
        "PINECONE_NAMESPACE": "test_namespace",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test_supabase_key",
        "VECTOR_STORE_TYPE": "pinecone",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "LLM_MODEL": "gemini-1.5-flash",
        "TEMPERATURE": "0.1",
        "MAX_TOKENS": "1000",
        "MAX_RESULTS": "5",
        "TIMEOUT_SECONDS": "25"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_rag_config():
    """Fixture providing mock RAG configuration"""
    return {
        "google_api_key": "test_google_key",
        "pinecone_api_key": "test_pinecone_key",
        "pinecone_environment": "test_env",
        "pinecone_index_name": "test_index",
        "pinecone_namespace": "test_namespace",
        "supabase_url": "https://test.supabase.co",
        "supabase_key": "test_supabase_key",
        "vector_store_type": "pinecone",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "llm_model": "gemini-1.5-flash",
        "temperature": 0.1,
        "max_tokens": 1000,
        "max_results": 5,
        "timeout_seconds": 25
    }


@pytest.fixture
def mock_embeddings():
    """Fixture providing mock embeddings"""
    return [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.6, 0.7, 0.8, 0.9, 1.0],
        [0.2, 0.4, 0.6, 0.8, 1.0]
    ]


@pytest.fixture
def mock_documents():
    """Fixture providing mock document data"""
    return [
        {
            "id": "doc1",
            "text": "Programs help build confidence through structured activities and peer support.",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
            "charity_name": "YCUK",
            "age_group": "16-18",
            "gender": "Female",
            "question_text": "How has this program impacted your confidence?",
            "question_type": "open",
            "created_at": "2024-01-01T10:00:00Z"
        },
        {
            "id": "doc2",
            "text": "I made many friends and learned to work as part of a team.",
            "embedding": [0.6, 0.7, 0.8, 0.9, 1.0],
            "charity_name": "Palace for Life",
            "age_group": "13-15",
            "gender": "Male",
            "question_text": "What did you gain from participating?",
            "question_type": "open",
            "created_at": "2024-01-01T11:00:00Z"
        },
        {
            "id": "doc3",
            "text": "The creative workshops helped me express myself and discover new talents.",
            "embedding": [0.2, 0.4, 0.6, 0.8, 1.0],
            "charity_name": "YCUK",
            "age_group": "19-25",
            "gender": "Female",
            "question_text": "Which activities were most meaningful to you?",
            "question_type": "open",
            "created_at": "2024-01-01T12:00:00Z"
        }
    ]


@pytest.fixture
def mock_search_results():
    """Fixture providing mock vector search results"""
    return [
        {
            "id": "doc1",
            "score": 0.95,
            "text": "Programs help build confidence through structured activities and peer support.",
            "organization": "YCUK",
            "age_group": "16-18",
            "gender": "Female",
            "question_text": "How has this program impacted your confidence?"
        },
        {
            "id": "doc2",
            "score": 0.87,
            "text": "I made many friends and learned to work as part of a team.",
            "organization": "Palace for Life",
            "age_group": "13-15",
            "gender": "Male",
            "question_text": "What did you gain from participating?"
        }
    ]


@pytest.fixture
def mock_rag_response():
    """Fixture providing mock RAG engine response"""
    return {
        'question': 'How do programs build confidence?',
        'answer': 'Based on survey responses, programs build confidence through structured activities, peer support, and skill development opportunities.',
        'source_documents': [
            {
                'text': 'Programs help build confidence through structured activities and peer support.',
                'organization': 'YCUK',
                'age_group': '16-18',
                'gender': 'Female'
            }
        ],
        'evidence_count': 1,
        'organizations': ['YCUK'],
        'age_groups': ['16-18'],
        'genders': ['Female'],
        'system_type': 'serverless_rag',
        'processing_time': 1.5
    }


@pytest.fixture
def mock_sentence_transformer():
    """Fixture providing mock SentenceTransformer"""
    mock_model = Mock()
    mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
    mock_model.eval.return_value = None
    return mock_model


@pytest.fixture
def mock_google_llm():
    """Fixture providing mock Google LLM"""
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "This is a test response from the LLM based on survey data."
    mock_llm.invoke.return_value = mock_response
    return mock_llm


@pytest.fixture
def mock_pinecone_client():
    """Fixture providing mock Pinecone client"""
    mock_client = Mock()
    mock_index = Mock()
    
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
    
    # Mock stats
    mock_stats = Mock()
    mock_stats.total_vector_count = 1000
    mock_stats.dimension = 384
    mock_stats.index_fullness = 0.02
    mock_stats.namespaces = {"test": Mock()}
    mock_index.describe_index_stats.return_value = mock_stats
    
    mock_client.Index.return_value = mock_index
    return mock_client, mock_index


@pytest.fixture
def mock_supabase_client():
    """Fixture providing mock Supabase client"""
    mock_client = Mock()
    mock_table = Mock()
    mock_query = Mock()
    
    # Mock query chain
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.in_.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
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
    mock_results.count = 1000
    mock_query.execute.return_value = mock_results
    
    # Mock upsert and delete
    mock_upsert = Mock()
    mock_delete = Mock()
    mock_table.upsert.return_value = mock_upsert
    mock_table.delete.return_value = mock_delete
    mock_delete.in_.return_value = mock_delete
    mock_upsert.execute.return_value = Mock()
    mock_delete.execute.return_value = Mock()
    
    return mock_client


@pytest.fixture
def mock_rag_engine():
    """Fixture providing mock RAG engine"""
    mock_engine = Mock()
    mock_engine.process_query.return_value = {
        'question': 'Test query',
        'answer': 'Test answer based on survey data',
        'source_documents': [{'text': 'Test doc', 'organization': 'Test Org'}],
        'evidence_count': 1,
        'organizations': ['Test Org'],
        'age_groups': ['16-18'],
        'genders': ['Male'],
        'processing_time': 1.5
    }
    return mock_engine


class TestHelpers:
    """Helper class with common test utilities"""
    
    @staticmethod
    def assert_valid_embedding(embedding: List[float], expected_dim: int = 5):
        """Assert that an embedding is valid"""
        assert isinstance(embedding, list)
        assert len(embedding) == expected_dim
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    @staticmethod
    def assert_valid_rag_response(response: Dict[str, Any]):
        """Assert that a RAG response has the expected structure"""
        required_keys = [
            'question', 'answer', 'source_documents', 'evidence_count',
            'organizations', 'age_groups', 'processing_time'
        ]
        for key in required_keys:
            assert key in response, f"Missing key: {key}"
        
        assert isinstance(response['source_documents'], list)
        assert isinstance(response['evidence_count'], int)
        assert isinstance(response['organizations'], list)
        assert isinstance(response['age_groups'], list)
        assert isinstance(response['processing_time'], (int, float))
    
    @staticmethod
    def assert_valid_search_results(results: List[Dict[str, Any]]):
        """Assert that search results have the expected structure"""
        for result in results:
            required_keys = ['id', 'score', 'text', 'organization', 'age_group', 'gender']
            for key in required_keys:
                assert key in result, f"Missing key: {key} in result: {result}"
            
            assert isinstance(result['score'], (int, float))
            assert 0 <= result['score'] <= 1, f"Invalid score: {result['score']}"
    
    @staticmethod
    def create_mock_conversation_turn(user_message: str = "Test message", 
                                    assistant_response: str = "Test response"):
        """Create a mock conversation turn"""
        from conversation import ConversationTurn
        return ConversationTurn(
            timestamp="2024-01-01T12:00:00",
            user_message=user_message,
            assistant_response=assistant_response,
            evidence_count=1,
            organizations=["Test Org"],
            age_groups=["16-18"],
            processing_time=1.0
        )


@pytest.fixture
def test_helpers():
    """Fixture providing test helper utilities"""
    return TestHelpers


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ["batch", "large", "performance"]):
            item.add_marker(pytest.mark.slow)