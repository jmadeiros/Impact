"""
Database setup script for the Impact Intelligence Platform.
This script helps initialize the Supabase database with proper vector extensions and functions.
Migrated from setup_database.py with updated imports
"""

from supabase import create_client
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from impact.shared.config.base import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

def setup_supabase_vector_search():
    """
    Set up Supabase for vector search functionality.
    This creates the necessary database function for similarity search.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # SQL to create the vector search function
    vector_search_function = \"\"\"
    CREATE OR REPLACE FUNCTION match_responses (
        query_embedding vector(768),
        match_threshold float DEFAULT 0.78,
        match_count int DEFAULT 10,
        filter jsonb DEFAULT '{}'
    )
    RETURNS TABLE (
        response_id int,
        participant_id text,
        charity_name text,
        age_group text,
        gender text,
        question_id text,
        response_value text,
        thematic_tags text[],
        similarity float
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            r.response_id,
            r.participant_id,
            r.charity_name,
            r.age_group,
            r.gender,
            r.question_id,
            r.response_value,
            r.thematic_tags,
            1 - (r.embedding <=> query_embedding) as similarity
        FROM responses r
        WHERE 1 - (r.embedding <=> query_embedding) > match_threshold
        ORDER BY r.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$;
    \"\"\"
    
    try:
        # Execute the function creation
        result = supabase.rpc('exec_sql', {'sql': vector_search_function}).execute()
        print("✅ Vector search function created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create vector search function: {str(e)}")
        return False

def check_database_setup():
    """Check if database tables exist and are accessible."""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check questions table
        questions_result = supabase.table("questions").select("count", count="exact").execute()
        questions_count = questions_result.count
        
        # Check responses table  
        responses_result = supabase.table("responses").select("count", count="exact").execute()
        responses_count = responses_result.count
        
        print(f"✅ Database accessible:")
        print(f"   Questions: {questions_count} rows")
        print(f"   Responses: {responses_count} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Database access failed: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Checking database setup...")
    if check_database_setup():
        print("✅ Database tables accessible")
    else:
        print("❌ Database setup issues detected")
        
    print("\\nSetting up vector search...")
    if setup_supabase_vector_search():
        print("✅ Vector search function created")
    else:
        print("❌ Vector search setup failed")