"""
Database connection utilities
Migrated from test_connection.py with updated imports
"""

import asyncio
import logging
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import sys
import os

# Import configuration
from impact.shared.config.base import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_connection():
    """Test Supabase database connection and basic queries."""
    try:
        print("🔍 Testing Supabase connection...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test basic connection
        result = supabase.table("questions").select("count", count="exact").execute()
        questions_count = result.count
        
        result = supabase.table("responses").select("count", count="exact").execute()  
        responses_count = result.count
        
        print(f"✅ Supabase connected successfully!")
        print(f"   Questions table: {questions_count} rows")
        print(f"   Responses table: {responses_count} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

async def test_google_ai_connection():
    """Test Google AI API connection."""
    try:
        print("🔍 Testing Google AI connection...")
        
        # Test LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1
        )
        
        response = llm.invoke("Say 'Hello from Google AI!'")
        print(f"✅ Google AI LLM connected: {response.content[:50]}...")
        
        # Test embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        
        test_embedding = embeddings.embed_query("test query")
        print(f"✅ Google AI Embeddings connected: {len(test_embedding)} dimensions")
        
        return True
        
    except Exception as e:
        print(f"❌ Google AI connection failed: {str(e)}")
        return False

async def test_all_connections():
    """Test all system connections."""
    print("🚀 TESTING ALL CONNECTIONS")
    print("=" * 50)
    
    supabase_ok = await test_supabase_connection()
    google_ai_ok = await test_google_ai_connection()
    
    print("\\n" + "=" * 50)
    if supabase_ok and google_ai_ok:
        print("✅ ALL CONNECTIONS SUCCESSFUL!")
        print("🎉 Your system is ready to use!")
    else:
        print("❌ Some connections failed")
        print("💡 Check your .env file and API keys")
    
    return supabase_ok and google_ai_ok

if __name__ == "__main__":
    asyncio.run(test_all_connections())