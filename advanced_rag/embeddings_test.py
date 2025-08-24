"""
Test embedding generation and similarity search
Step 1: Get embeddings working independently
"""
import os
import sys
sys.path.append('..')

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple
import json
from config_advanced import EMBEDDING_MODEL

class EmbeddingTester:
    def __init__(self):
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Embedding model loaded successfully")
    
    def test_basic_embeddings(self):
        """Test basic embedding generation"""
        print("\n🧪 Testing Basic Embeddings")
        print("-" * 40)
        
        test_texts = [
            "I gained confidence through the program",
            "The program helped me build self-esteem",
            "I made new friends and connections",
            "The creative activities were amazing",
            "I learned leadership skills"
        ]
        
        embeddings = self.model.encode(test_texts)
        print(f"Generated embeddings shape: {embeddings.shape}")
        print(f"Embedding dimension: {embeddings.shape[1]}")
        
        return embeddings, test_texts
    
    def test_similarity_search(self, embeddings: np.ndarray, texts: List[str]):
        """Test similarity search functionality"""
        print("\n🔍 Testing Similarity Search")
        print("-" * 40)
        
        # Test queries
        queries = [
            "How did the program boost confidence?",
            "Tell me about making friends",
            "What creative work was done?"
        ]
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            query_embedding = self.model.encode([query])
            
            # Calculate similarities
            similarities = np.dot(embeddings, query_embedding.T).flatten()
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:3]
            
            print("Top matches:")
            for i, idx in enumerate(top_indices):
                print(f"  {i+1}. {texts[idx]} (similarity: {similarities[idx]:.3f})")
    
    def test_with_sample_data(self):
        """Test with actual survey response data"""
        print("\n📊 Testing with Sample Survey Data")
        print("-" * 40)
        
        # Sample responses from our data
        sample_responses = [
            "I really enjoyed making the film and working as a team. It was great to have our ideas heard and to be able to put them into practice.",
            "The program helped me gain confidence in speaking up and sharing my ideas with others.",
            "I made some really good friends and learned how to work better in a group setting.",
            "The creative activities like filmmaking and storytelling were my favorite parts of the program.",
            "I learned leadership skills and how to take initiative on projects that matter to me.",
            "The program was challenging but it helped me become more resilient and determined.",
            "I feel more confident about my future and have a clearer idea of what I want to do"
        ]
        
        # Generate embeddings
        embeddings = self.model.encode(sample_responses)
        
        # Test semantic queries
        semantic_queries = [
            "How do programs build confidence in young people?",
            "What helps teenagers make friends and social connections?",
            "Show me evidence of creative engagement",
            "How do participants develop leadership abilities?",
            "What impact on future aspirations?"
        ]
        
        for query in semantic_queries:
            print(f"\nSemantic Query: '{query}'")
            query_embedding = self.model.encode([query])
            similarities = np.dot(embeddings, query_embedding.T).flatten()
            
            # Get top 2 matches
            top_indices = np.argsort(similarities)[::-1][:2]
            
            for i, idx in enumerate(top_indices):
                if similarities[idx] > 0.3:  # Threshold for relevance
                    print(f"  Match {i+1}: {sample_responses[idx][:80]}...")
                    print(f"    Similarity: {similarities[idx]:.3f}")
    
    def run_all_tests(self):
        """Run all embedding tests"""
        print("🚀 EMBEDDING SYSTEM TESTS")
        print("=" * 50)
        
        try:
            # Basic tests
            embeddings, texts = self.test_basic_embeddings()
            self.test_similarity_search(embeddings, texts)
            self.test_with_sample_data()
            
            print("\n✅ All embedding tests passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Embedding test failed: {str(e)}")
            return False

if __name__ == "__main__":
    tester = EmbeddingTester()
    tester.run_all_tests()