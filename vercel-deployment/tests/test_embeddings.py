"""
Unit tests for ServerlessEmbeddingClient
Tests embedding generation, caching, batch processing, and performance optimizations
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import hashlib
from typing import List

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from embeddings import (
    ServerlessEmbeddingClient, EmbeddingCache, 
    create_embedding_client, quick_embed, batch_embed
)

def create_mock_numpy_array(data):
    """Create a mock that behaves like a numpy array with tolist() method"""
    mock_array = Mock()
    mock_array.tolist.return_value = data
    return mock_array


class TestServerlessEmbeddingClient(unittest.TestCase):
    """Test cases for ServerlessEmbeddingClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    def test_initialization(self):
        """Test embedding client initialization"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        self.assertEqual(client.model_name, self.model_name)
        self.assertIsNone(client._model)  # Should be lazy-loaded
        self.assertEqual(client._cache, {})
        self.assertEqual(client.stats['cache_hits'], 0)
        self.assertEqual(client.stats['embeddings_generated'], 0)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_model_initialization(self, mock_transformer_class):
        """Test lazy model initialization"""
        mock_model = Mock()
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Access model property to trigger initialization
        model = client.model
        
        self.assertEqual(model, mock_model)
        mock_transformer_class.assert_called_once_with(self.model_name)
        mock_model.eval.assert_called_once()
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_model_initialization_failure(self, mock_transformer_class):
        """Test model initialization failure"""
        mock_transformer_class.side_effect = Exception("Model loading failed")
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        with self.assertRaises(Exception):
            _ = client.model
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        text = "test text"
        expected_key = hashlib.md5(text.encode('utf-8')).hexdigest()
        actual_key = client._get_cache_key(text)
        
        self.assertEqual(actual_key, expected_key)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_single_success(self, mock_transformer_class):
        """Test successful single text encoding"""
        mock_model = Mock()
        mock_model.encode.return_value = [create_mock_numpy_array(create_mock_numpy_array(self.test_embedding))]
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        text = "test text"
        embedding = client.encode_single(text)
        
        self.assertEqual(embedding, self.test_embedding)
        mock_model.encode.assert_called_once_with([text])
        self.assertEqual(client.stats['embeddings_generated'], 1)
        self.assertEqual(client.stats['cache_misses'], 1)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_single_with_caching(self, mock_transformer_class):
        """Test single encoding with caching"""
        mock_model = Mock()
        mock_model.encode.return_value = [create_mock_numpy_array(create_mock_numpy_array(self.test_embedding))]
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        text = "test text"
        
        # First call should generate embedding
        embedding1 = client.encode_single(text, use_cache=True)
        self.assertEqual(embedding1, self.test_embedding)
        self.assertEqual(client.stats['cache_misses'], 1)
        self.assertEqual(client.stats['cache_hits'], 0)
        
        # Second call should use cache
        embedding2 = client.encode_single(text, use_cache=True)
        self.assertEqual(embedding2, self.test_embedding)
        self.assertEqual(client.stats['cache_misses'], 1)
        self.assertEqual(client.stats['cache_hits'], 1)
        
        # Model should only be called once
        mock_model.encode.assert_called_once()
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_single_no_cache(self, mock_transformer_class):
        """Test single encoding without caching"""
        mock_model = Mock()
        mock_model.encode.return_value = [create_mock_numpy_array(self.test_embedding)]
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        text = "test text"
        
        # Two calls without caching
        embedding1 = client.encode_single(text, use_cache=False)
        embedding2 = client.encode_single(text, use_cache=False)
        
        self.assertEqual(embedding1, self.test_embedding)
        self.assertEqual(embedding2, self.test_embedding)
        
        # Model should be called twice
        self.assertEqual(mock_model.encode.call_count, 2)
        self.assertEqual(client.stats['embeddings_generated'], 2)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_single_failure(self, mock_transformer_class):
        """Test single encoding failure"""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Encoding failed")
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        text = "test text"
        embedding = client.encode_single(text)
        
        self.assertEqual(embedding, [])
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_batch_success(self, mock_transformer_class):
        """Test successful batch encoding"""
        mock_model = Mock()
        batch_embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        # Mock numpy array behavior for batch
        mock_arrays = [create_mock_numpy_array(emb) for emb in batch_embeddings]
        mock_result = Mock()
        mock_result.tolist.return_value = batch_embeddings
        mock_model.encode.return_value = mock_result
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        texts = ["text 1", "text 2", "text 3"]
        embeddings = client.encode_batch(texts, use_cache=False)
        
        self.assertEqual(len(embeddings), 3)
        self.assertEqual(embeddings, batch_embeddings)
        mock_model.encode.assert_called_once_with(texts)
        self.assertEqual(client.stats['embeddings_generated'], 3)
        self.assertEqual(client.stats['batch_operations'], 1)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_batch_with_caching(self, mock_transformer_class):
        """Test batch encoding with partial caching"""
        mock_model = Mock()
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Pre-populate cache with one embedding
        cached_text = "cached text"
        cached_embedding = [0.1, 0.2, 0.3]
        cache_key = client._get_cache_key(cached_text)
        client._cache[cache_key] = cached_embedding
        
        # Mock encoding for uncached texts
        uncached_embeddings = [[0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        mock_model.encode.return_value = uncached_embeddings
        
        texts = [cached_text, "new text 1", "new text 2"]
        embeddings = client.encode_batch(texts, use_cache=True)
        
        # Should return embeddings in original order
        self.assertEqual(len(embeddings), 3)
        self.assertEqual(embeddings[0], cached_embedding)  # From cache
        self.assertEqual(embeddings[1], uncached_embeddings[0])  # Generated
        self.assertEqual(embeddings[2], uncached_embeddings[1])  # Generated
        
        # Should only encode uncached texts
        mock_model.encode.assert_called_once_with(["new text 1", "new text 2"])
        
        # Stats should reflect cache usage
        self.assertEqual(client.stats['cache_hits'], 1)
        self.assertEqual(client.stats['cache_misses'], 2)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_batch_with_batching(self, mock_transformer_class):
        """Test batch encoding with internal batching"""
        mock_model = Mock()
        
        # Mock multiple batch calls
        batch1_embeddings = [[0.1, 0.2], [0.3, 0.4]]
        batch2_embeddings = [[0.5, 0.6]]
        mock_model.encode.side_effect = [batch1_embeddings, batch2_embeddings]
        
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        texts = ["text 1", "text 2", "text 3"]
        embeddings = client.encode_batch(texts, batch_size=2, use_cache=False)
        
        # Should combine results from both batches
        expected_embeddings = batch1_embeddings + batch2_embeddings
        self.assertEqual(embeddings, expected_embeddings)
        
        # Should call encode twice due to batching
        self.assertEqual(mock_model.encode.call_count, 2)
        mock_model.encode.assert_any_call(["text 1", "text 2"])
        mock_model.encode.assert_any_call(["text 3"])
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_batch_empty_list(self, mock_transformer_class):
        """Test batch encoding with empty list"""
        mock_model = Mock()
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        embeddings = client.encode_batch([])
        
        self.assertEqual(embeddings, [])
        mock_model.encode.assert_not_called()
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_encode_batch_failure(self, mock_transformer_class):
        """Test batch encoding failure"""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Batch encoding failed")
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        texts = ["text 1", "text 2"]
        embeddings = client.encode_batch(texts, use_cache=False)
        
        # Should return empty embeddings for each text
        self.assertEqual(embeddings, [[], []])
    
    def test_similarity_calculation(self):
        """Test cosine similarity calculation"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = client.similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 1.0, places=5)
        
        # Test orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = client.similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0, places=5)
        
        # Test opposite vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = client.similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0, places=5)
    
    def test_similarity_zero_vector(self):
        """Test similarity with zero vector"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = client.similarity(vec1, vec2)
        
        self.assertEqual(similarity, 0.0)
    
    def test_find_most_similar(self):
        """Test finding most similar embeddings"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        query_embedding = [1.0, 0.0, 0.0]
        candidate_embeddings = [
            [1.0, 0.0, 0.0],    # similarity = 1.0
            [0.0, 1.0, 0.0],    # similarity = 0.0
            [-1.0, 0.0, 0.0],   # similarity = -1.0
            [0.5, 0.5, 0.0]     # similarity ≈ 0.707
        ]
        
        results = client.find_most_similar(query_embedding, candidate_embeddings, top_k=3)
        
        # Should return top 3 by similarity (descending order)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['index'], 0)  # Highest similarity
        self.assertAlmostEqual(results[0]['similarity'], 1.0, places=5)
        self.assertEqual(results[1]['index'], 3)  # Second highest
        self.assertAlmostEqual(results[1]['similarity'], 0.707, places=2)
        self.assertEqual(results[2]['index'], 1)  # Third highest
        self.assertAlmostEqual(results[2]['similarity'], 0.0, places=5)
    
    def test_find_most_similar_empty_candidates(self):
        """Test finding similar with empty candidates"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        query_embedding = [1.0, 0.0, 0.0]
        results = client.find_most_similar(query_embedding, [], top_k=5)
        
        self.assertEqual(results, [])
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Simulate some activity
        client.stats['cache_hits'] = 10
        client.stats['cache_misses'] = 5
        client.stats['embeddings_generated'] = 5
        client._cache = {'key1': [0.1, 0.2], 'key2': [0.3, 0.4]}
        
        stats = client.get_stats()
        
        self.assertEqual(stats['model_name'], self.model_name)
        self.assertEqual(stats['cache_size'], 2)
        self.assertEqual(stats['stats']['cache_hits'], 10)
        self.assertEqual(stats['stats']['cache_misses'], 5)
        self.assertEqual(stats['stats']['embeddings_generated'], 5)
        self.assertAlmostEqual(stats['cache_hit_rate'], 10/15, places=5)
    
    def test_clear_cache(self):
        """Test cache clearing"""
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Add some items to cache
        client._cache = {'key1': [0.1, 0.2], 'key2': [0.3, 0.4]}
        
        client.clear_cache()
        
        self.assertEqual(client._cache, {})
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_warmup(self, mock_transformer_class):
        """Test model warmup"""
        mock_model = Mock()
        mock_model.encode.return_value = [create_mock_numpy_array([0.1, 0.2], [0.3, 0.4], [0.5, 0.6])]
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Test warmup with default texts
        client.warmup()
        
        # Should have called encode once for warmup
        mock_model.encode.assert_called_once()
        
        # Test warmup with custom texts
        custom_texts = ["custom text 1", "custom text 2"]
        client.warmup(custom_texts)
        
        # Should have called encode again
        self.assertEqual(mock_model.encode.call_count, 2)
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_warmup_failure(self, mock_transformer_class):
        """Test warmup failure handling"""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Warmup failed")
        mock_transformer_class.return_value = mock_model
        
        client = ServerlessEmbeddingClient(self.model_name)
        
        # Should not raise exception
        client.warmup()


class TestEmbeddingCache(unittest.TestCase):
    """Test cases for EmbeddingCache"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cache = EmbeddingCache(max_size=3)
    
    def test_initialization(self):
        """Test cache initialization"""
        self.assertEqual(self.cache.max_size, 3)
        self.assertEqual(self.cache.cache, {})
        self.assertEqual(self.cache.access_count, {})
    
    def test_set_and_get(self):
        """Test setting and getting cache entries"""
        text = "test text"
        embedding = [0.1, 0.2, 0.3]
        
        # Set embedding
        self.cache.set(text, embedding)
        
        # Get embedding
        retrieved = self.cache.get(text)
        
        self.assertEqual(retrieved, embedding)
        self.assertEqual(self.cache.size(), 1)
    
    def test_get_nonexistent(self):
        """Test getting non-existent cache entry"""
        result = self.cache.get("nonexistent text")
        self.assertIsNone(result)
    
    def test_access_count_tracking(self):
        """Test access count tracking"""
        text = "test text"
        embedding = [0.1, 0.2, 0.3]
        
        self.cache.set(text, embedding)
        
        # Access multiple times
        self.cache.get(text)
        self.cache.get(text)
        self.cache.get(text)
        
        key = hashlib.md5(text.encode('utf-8')).hexdigest()
        self.assertEqual(self.cache.access_count[key], 4)  # 1 from set + 3 from gets
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Fill cache to capacity
        for i in range(3):
            text = f"text {i}"
            embedding = [0.1 * i, 0.2 * i, 0.3 * i]
            self.cache.set(text, embedding)
        
        # Access text 1 to make it more recently used
        self.cache.get("text 1")
        
        # Add new item (should evict text 0, the least recently used)
        self.cache.set("text 3", [0.4, 0.5, 0.6])
        
        # text 0 should be evicted
        self.assertIsNone(self.cache.get("text 0"))
        # text 1 should still be there
        self.assertIsNotNone(self.cache.get("text 1"))
        # text 3 should be there
        self.assertIsNotNone(self.cache.get("text 3"))
        
        self.assertEqual(self.cache.size(), 3)
    
    def test_update_existing_entry(self):
        """Test updating existing cache entry"""
        text = "test text"
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.4, 0.5, 0.6]
        
        # Set initial embedding
        self.cache.set(text, embedding1)
        self.assertEqual(self.cache.size(), 1)
        
        # Update with new embedding
        self.cache.set(text, embedding2)
        self.assertEqual(self.cache.size(), 1)  # Size shouldn't change
        
        # Should return updated embedding
        retrieved = self.cache.get(text)
        self.assertEqual(retrieved, embedding2)


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions"""
    
    @patch('embeddings.ServerlessEmbeddingClient')
    def test_create_embedding_client_default(self, mock_client_class):
        """Test creating embedding client with default model"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        client = create_embedding_client()
        
        self.assertEqual(client, mock_client)
        mock_client_class.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")
    
    @patch('embeddings.ServerlessEmbeddingClient')
    def test_create_embedding_client_custom_model(self, mock_client_class):
        """Test creating embedding client with custom model"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        custom_model = "custom-model"
        client = create_embedding_client(custom_model)
        
        self.assertEqual(client, mock_client)
        mock_client_class.assert_called_once_with(custom_model)
    
    @patch.dict(os.environ, {"EMBEDDING_MODEL": "env-model"})
    @patch('embeddings.ServerlessEmbeddingClient')
    def test_create_embedding_client_from_env(self, mock_client_class):
        """Test creating embedding client from environment variable"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        client = create_embedding_client()
        
        self.assertEqual(client, mock_client)
        mock_client_class.assert_called_once_with("env-model")
    
    @patch('embeddings.create_embedding_client')
    def test_quick_embed(self, mock_create_client):
        """Test quick embedding function"""
        mock_client = Mock()
        mock_client.encode_single.return_value = [0.1, 0.2, 0.3]
        mock_create_client.return_value = mock_client
        
        text = "test text"
        embedding = quick_embed(text)
        
        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        mock_client.encode_single.assert_called_once_with(text)
    
    @patch('embeddings.create_embedding_client')
    def test_batch_embed(self, mock_create_client):
        """Test batch embedding function"""
        mock_client = Mock()
        mock_embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_client.encode_batch.return_value = mock_embeddings
        mock_create_client.return_value = mock_client
        
        texts = ["text 1", "text 2"]
        embeddings = batch_embed(texts, batch_size=16)
        
        self.assertEqual(embeddings, mock_embeddings)
        mock_client.encode_batch.assert_called_once_with(texts, batch_size=16)


if __name__ == '__main__':
    unittest.main()