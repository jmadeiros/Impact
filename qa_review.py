"""
Quality Assurance script for reviewing AI-generated thematic tags.
This script helps human reviewers validate and correct thematic tags.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class QAReviewer:
    def __init__(self):
        self.reviewed_count = 0
        self.corrected_count = 0
    
    async def get_low_confidence_tags(self, confidence_threshold: float = 0.6, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch responses with low-confidence thematic tags for human review.
        """
        try:
            result = supabase.table("responses").select("""
                response_id,
                response_value,
                thematic_tags,
                tag_confidence,
                charity_name,
                age_group,
                gender,
                questions(question_text)
            """).lt("tag_confidence", confidence_threshold).order("tag_confidence").limit(limit).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error fetching low confidence tags: {str(e)}")
            return []
    
    async def get_random_sample_for_audit(self, sample_size: int = 10) -> List[Dict[str, Any]]:
        """
        Get a random sample of responses for quality audit.
        """
        try:
            # Get total count first
            count_result = supabase.table("responses").select("response_id", count="exact").not_.is_("thematic_tags", "null").execute()
            total_count = count_result.count
            
            if total_count == 0:
                return []
            
            # Get random sample using TABLESAMPLE (if supported) or ORDER BY RANDOM()
            result = supabase.rpc("get_random_responses", {"sample_size": sample_size}).execute()
            
            if not result.data:
                # Fallback: get responses with random ordering
                result = supabase.table("responses").select("""
                    response_id,
                    response_value,
                    thematic_tags,
                    tag_confidence,
                    charity_name,
                    age_group,
                    gender,
                    questions(question_text)
                """).not_.is_("thematic_tags", "null").limit(sample_size).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error fetching random sample: {str(e)}")
            return []
    
    def display_response_for_review(self, response_data: Dict[str, Any]) -> None:
        """
        Display a response in a human-readable format for review.
        """
        print("\n" + "="*80)
        print(f"RESPONSE ID: {response_data['response_id']}")
        print(f"CONFIDENCE: {response_data.get('tag_confidence', 'N/A')}")
        print("-"*80)
        
        # Context
        print(f"Organization: {response_data.get('charity_name', 'Unknown')}")
        print(f"Participant: {response_data.get('age_group', 'Unknown')} {response_data.get('gender', 'participant')}")
        
        if response_data.get('questions'):
            print(f"Question: {response_data['questions']['question_text']}")
        
        print("-"*80)
        
        # Response text
        response_text = response_data['response_value']
        if len(response_text) > 300:
            print(f"Response: {response_text[:300]}...")
        else:
            print(f"Response: {response_text}")
        
        print("-"*80)
        
        # Current tags
        current_tags = response_data.get('thematic_tags', [])
        print(f"Current Tags: {', '.join(current_tags) if current_tags else 'None'}")
        print("="*80)
    
    async def review_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Interactive review of a single response.
        Returns True if changes were made.
        """
        self.display_response_for_review(response_data)
        
        current_tags = response_data.get('thematic_tags', [])
        
        print("\nReview Options:")
        print("1. Accept current tags (press Enter)")
        print("2. Modify tags (type new tags separated by commas)")
        print("3. Skip this response (type 'skip')")
        print("4. Quit review session (type 'quit')")
        
        user_input = input("\nYour choice: ").strip()
        
        if user_input.lower() == 'quit':
            return False
        elif user_input.lower() == 'skip':
            return True
        elif user_input == '':
            # Accept current tags - mark as human-reviewed
            await self.mark_as_reviewed(response_data['response_id'], current_tags, 1.0)
            self.reviewed_count += 1
            print("✅ Tags accepted and marked as human-reviewed")
            return True
        else:
            # Parse new tags
            new_tags = [tag.strip() for tag in user_input.split(',') if tag.strip()]
            
            if new_tags:
                await self.mark_as_reviewed(response_data['response_id'], new_tags, 1.0)
                self.reviewed_count += 1
                self.corrected_count += 1
                print(f"✅ Tags updated to: {', '.join(new_tags)}")
            else:
                print("❌ No valid tags provided. Skipping.")
            
            return True
    
    async def mark_as_reviewed(self, response_id: int, final_tags: List[str], confidence: float) -> bool:
        """
        Mark a response as human-reviewed with final tags.
        """
        try:
            result = supabase.table("responses").update({
                "thematic_tags": final_tags,
                "tag_confidence": confidence,
                "human_reviewed": True,
                "reviewed_at": "now()"
            }).eq("response_id", response_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error marking response as reviewed: {str(e)}")
            return False
    
    async def run_qa_session(self, mode: str = "low_confidence", limit: int = 10):
        """
        Run an interactive QA session.
        """
        print("Impact Intelligence Platform - QA Review Session")
        print("="*60)
        
        if mode == "low_confidence":
            print(f"Reviewing {limit} responses with low-confidence tags...")
            responses = await self.get_low_confidence_tags(limit=limit)
        else:
            print(f"Reviewing {limit} random responses for quality audit...")
            responses = await self.get_random_sample_for_audit(sample_size=limit)
        
        if not responses:
            print("No responses found for review.")
            return
        
        print(f"Found {len(responses)} responses to review.\n")
        
        for i, response_data in enumerate(responses):
            print(f"\n--- Review {i+1}/{len(responses)} ---")
            
            continue_review = await self.review_response(response_data)
            if not continue_review:
                break
        
        print(f"\n🎉 QA Session Complete!")
        print(f"Reviewed: {self.reviewed_count} responses")
        print(f"Corrected: {self.corrected_count} responses")
        print(f"Accuracy Rate: {((self.reviewed_count - self.corrected_count) / max(self.reviewed_count, 1)) * 100:.1f}%")

async def create_qa_database_functions():
    """
    Create database functions to support QA operations.
    """
    try:
        # Add columns for human review tracking if they don't exist
        alter_table_sql = """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='responses' AND column_name='human_reviewed') THEN
                ALTER TABLE responses ADD COLUMN human_reviewed BOOLEAN DEFAULT FALSE;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='responses' AND column_name='reviewed_at') THEN
                ALTER TABLE responses ADD COLUMN reviewed_at TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='responses' AND column_name='tag_confidence') THEN
                ALTER TABLE responses ADD COLUMN tag_confidence FLOAT DEFAULT 0.5;
            END IF;
        END $$;
        """
        
        # Function to get random responses
        random_function_sql = """
        CREATE OR REPLACE FUNCTION get_random_responses(sample_size INT)
        RETURNS TABLE (
            response_id INT,
            response_value TEXT,
            thematic_tags TEXT[],
            tag_confidence FLOAT,
            charity_name TEXT,
            age_group TEXT,
            gender TEXT,
            questions JSONB
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                r.response_id,
                r.response_value,
                r.thematic_tags,
                r.tag_confidence,
                r.charity_name,
                r.age_group,
                r.gender,
                to_jsonb(q.*) as questions
            FROM responses r
            LEFT JOIN questions q ON r.question_id = q.question_id
            WHERE r.thematic_tags IS NOT NULL
            ORDER BY RANDOM()
            LIMIT sample_size;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        supabase.rpc('exec_sql', {'sql': alter_table_sql}).execute()
        supabase.rpc('exec_sql', {'sql': random_function_sql}).execute()
        
        print("✅ QA database functions created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating QA functions: {str(e)}")
        print("❌ Failed to create QA database functions")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        print("Setting up QA database functions...")
        await create_qa_database_functions()
        
        print("\nQA Review Options:")
        print("1. Review low-confidence tags")
        print("2. Random quality audit")
        
        choice = input("Choose option (1 or 2): ").strip()
        limit = int(input("How many responses to review? (default 10): ").strip() or "10")
        
        reviewer = QAReviewer()
        
        if choice == "1":
            await reviewer.run_qa_session("low_confidence", limit)
        else:
            await reviewer.run_qa_session("random", limit)
    
    asyncio.run(main())