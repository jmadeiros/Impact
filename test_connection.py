"""
Test script to verify Supabase and Google AI connections.
Run this after setting up your .env file to ensure everything works.
"""

import asyncio
import logging
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from config import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY

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
        
        # Test sample data
        if questions_count > 0:
            sample_q = supabase.table("questions").select("*").limit(1).execute()
            print(f"   Sample question: {sample_q.data[0]['question_text'][:50]}...")
        
        if responses_count > 0:
            sample_r = supabase.table("responses").select("*").limit(1).execute()
            print(f"   Sample response: {sample_r.data[0]['response_value'][:50]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

async def test_google_ai_connection():
    """Test Google AI API connection."""
    try:
        print("\n🔍 Testing Google AI connection...")
        
        # Test LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1
        )
        
        response = llm.invoke("Say 'Hello from Gemini!' in exactly those words.")
        print(f"✅ Google AI LLM connected successfully!")
        print(f"   Response: {response.content}")
        
        # Test embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        
        test_embedding = await embeddings.aembed_query("test embedding")
        print(f"✅ Google AI Embeddings connected successfully!")
        print(f"   Embedding dimension: {len(test_embedding)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google AI connection failed: {str(e)}")
        return False

async def test_vector_search_setup():
    """Test if vector search is properly configured."""
    try:
        print("\n🔍 Testing vector search setup...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if pgvector extension is enabled
        result = supabase.rpc("exec_sql", {
            "sql": "SELECT * FROM pg_extension WHERE extname = 'vector';"
        }).execute()
        
        if result.data:
            print("✅ pgvector extension is installed")
        else:
            print("⚠️  pgvector extension not found - you may need to enable it in Supabase")
        
        # Check if embedding column exists
        result = supabase.rpc("exec_sql", {
            "sql": """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'responses' AND column_name = 'embedding';
            """
        }).execute()
        
        if result.data:
            print("✅ Embedding column exists in responses table")
        else:
            print("⚠️  Embedding column not found - you may need to add it")
            
        # Check if match_responses function exists
        result = supabase.rpc("exec_sql", {
            "sql": """
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name = 'match_responses';
            """
        }).execute()
        
        if result.data:
            print("✅ match_responses function exists")
        else:
            print("⚠️  match_responses function not found - run setup_database.py")
            
        return True
        
    except Exception as e:
        print(f"❌ Vector search setup check failed: {str(e)}")
        return False

async def main():
    """Run all connection tests."""
    print("Impact Intelligence Platform - Connection Test")
    print("=" * 50)
    
    supabase_ok = await test_supabase_connection()
    google_ai_ok = await test_google_ai_connection()
    vector_ok = await test_vector_search_setup()
    
    print("\n" + "=" * 50)
    if supabase_ok and google_ai_ok:
        print("🎉 All connections successful! Ready to run the platform.")
        
        if not vector_ok:
            print("\n⚠️  Vector search needs setup. Run:")
            print("   python setup_database.py")
            print("   python enrich_data.py")
    else:
        print("❌ Some connections failed. Check your .env file and API keys.")
        
        if not supabase_ok:
            print("\n🔧 Supabase troubleshooting:")
            print("   - Verify SUPABASE_URL is correct")
            print("   - Verify SUPABASE_KEY (use service_role for full access)")
            print("   - Check if tables exist in your Supabase project")
            
        if not google_ai_ok:
            print("\n🔧 Google AI troubleshooting:")
            print("   - Get API key from https://makersuite.google.com/app/apikey")
            print("   - Verify GOOGLE_API_KEY is correct")
            print("   - Check API quotas and billing")

if __name__ == "__main__":
    asyncio.run(main())