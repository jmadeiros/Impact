"""
Database setup script for the Impact Intelligence Platform.
This script helps initialize the Supabase database with proper vector extensions and functions.
"""

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

logger = logging.getLogger(__name__)

def setup_supabase_vector_search():
    """
    Set up Supabase for vector search functionality.
    This creates the necessary database function for similarity search.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # SQL to create the vector search function
    vector_search_function = """
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
    DECLARE
        filter_clause text := '';
    BEGIN
        -- Build dynamic filter clause
        IF filter != '{}' THEN
            filter_clause := 'AND ';
            IF filter ? 'charity_name' THEN
                filter_clause := filter_clause || 'charity_name = ''' || (filter->>'charity_name') || ''' AND ';
            END IF;
            IF filter ? 'age_group' THEN
                filter_clause := filter_clause || 'age_group = ''' || (filter->>'age_group') || ''' AND ';
            END IF;
            IF filter ? 'gender' THEN
                filter_clause := filter_clause || 'gender = ''' || (filter->>'gender') || ''' AND ';
            END IF;
            IF filter ? 'question_id' THEN
                filter_clause := filter_clause || 'question_id = ''' || (filter->>'question_id') || ''' AND ';
            END IF;
            -- Remove trailing 'AND '
            filter_clause := rtrim(filter_clause, 'AND ');
        END IF;
        
        RETURN QUERY EXECUTE
        'SELECT 
            r.response_id,
            r.participant_id,
            r.charity_name,
            r.age_group,
            r.gender,
            r.question_id,
            r.response_value,
            r.thematic_tags,
            1 - (r.embedding <=> $1) as similarity
        FROM responses r
        WHERE 1 - (r.embedding <=> $1) > $2 ' || filter_clause || '
        ORDER BY r.embedding <=> $1
        LIMIT $3'
        USING query_embedding, match_threshold, match_count;
    END;
    $$;
    """
    
    try:
        # Execute the function creation
        result = supabase.rpc('exec_sql', {'sql': vector_search_function}).execute()
        logger.info("Vector search function created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating vector search function: {str(e)}")
        logger.info("You may need to run this SQL manually in your Supabase SQL editor:")
        print(vector_search_function)
        return False

def check_database_setup():
    """
    Check if the database has the required tables and extensions.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Check if tables exist
        questions_result = supabase.table("questions").select("count", count="exact").execute()
        responses_result = supabase.table("responses").select("count", count="exact").execute()
        
        logger.info(f"Questions table: {questions_result.count} rows")
        logger.info(f"Responses table: {responses_result.count} rows")
        
        return True
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Checking database setup...")
    if check_database_setup():
        print("✅ Database tables accessible")
    else:
        print("❌ Database setup issues detected")
        
    print("\nSetting up vector search...")
    if setup_supabase_vector_search():
        print("✅ Vector search function created")
    else:
        print("❌ Vector search setup failed - check logs above")