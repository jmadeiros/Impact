"""
Advanced RAG Configuration - Additional settings for advanced system
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import base config
from .base import GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY

# Optional API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Optional for embeddings

# Vector Store Configuration
VECTOR_STORE_TYPE = "chroma"  # or "faiss"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, good quality
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Langchain Configuration
LLM_MODEL = "gemini-1.5-pro"
TEMPERATURE = 0.1
MAX_TOKENS = 1000

# Database Configuration
DB_TABLE_RESPONSES = "responses"
DB_TABLE_QUESTIONS = "questions"

# Paths
VECTOR_DB_PATH = "./vector_store"
CACHE_PATH = "./cache"