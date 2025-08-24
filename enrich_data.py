"""
Data enrichment script for the Impact Intelligence Platform.
This script processes raw survey data to generate embeddings and thematic tags.
"""

import asyncio
import logging
from typing import List, Dict, Any
from supabase import create_client
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from config import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY
import json

logger = logging.getLogger(__name__)

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.1
)

async def generate_thematic_tags(response_text: str, question_context: str = "") -> tuple[List[str], float]:
    """
    Generate thematic tags for a response using LLM analysis.
    Returns tuple of (tags, confidence_score).
    """
    tagging_prompt = PromptTemplate(
        input_variables=["response_text", "question_context"],
        template="""
Analyze this survey response and generate 3-5 thematic tags that capture the key concepts and themes.

Question Context: {question_context}
Response: "{response_text}"

Generate tags that would be useful for thematic filtering and search. Focus on:
- Emotional themes (resilience, confidence, anxiety, etc.)
- Activity types (creative, leadership, teamwork, etc.)
- Outcomes (skill-building, personal growth, social connection, etc.)
- Challenges (barriers, difficulties, fears, etc.)

Return a JSON object with tags and confidence score:
{
  "tags": ["resilience", "creative_expression", "confidence_building"],
  "confidence": 0.85
}

Confidence should be 0.0-1.0 based on how clearly the themes are expressed in the text.
"""
    )
    
    try:
        formatted_prompt = tagging_prompt.format(
            response_text=response_text,
            question_context=question_context
        )
        
        response = llm.invoke(formatted_prompt)
        
        # Parse the JSON response
        try:
            result = json.loads(response.content)
            if isinstance(result, dict) and "tags" in result:
                tags = result["tags"]
                confidence = result.get("confidence", 0.5)
                return tags if isinstance(tags, list) else [], confidence
            elif isinstance(result, list):
                # Fallback for old format
                return result, 0.5
            else:
                return [], 0.1
        except json.JSONDecodeError:
            # Fallback: extract tags from text response
            content = response.content.lower()
            fallback_tags = []
            
            # Basic keyword extraction
            if "resilience" in content or "resilient" in content:
                fallback_tags.append("resilience")
            if "creative" in content or "creativity" in content:
                fallback_tags.append("creative_expression")
            if "confidence" in content or "confident" in content:
                fallback_tags.append("confidence_building")
            if "leadership" in content or "leader" in content:
                fallback_tags.append("leadership")
            if "teamwork" in content or "collaboration" in content:
                fallback_tags.append("teamwork")
                
            return fallback_tags[:5], 0.3  # Lower confidence for fallback
            
    except Exception as e:
        logger.error(f"Error generating thematic tags: {str(e)}")
        return ["general_response"], 0.1

async def generate_embedding(text: str) -> List[float]:
    """
    Generate vector embedding for a text.
    """
    try:
        embedding_vector = await embeddings.aembed_query(text)
        return embedding_vector
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return []

async def enrich_single_response(response_data: Dict[str, Any]) -> bool:
    """
    Enrich a single response with embeddings and thematic tags.
    """
    try:
        response_id = response_data["response_id"]
        response_text = response_data["response_value"]
        question_text = response_data.get("question_text", "")
        
        logger.info(f"Enriching response {response_id}")
        
        # Generate thematic tags with confidence score
        thematic_tags, confidence_score = await generate_thematic_tags(response_text, question_text)
        
        # Generate embedding
        embedding_vector = await generate_embedding(response_text)
        
        if not embedding_vector:
            logger.warning(f"Failed to generate embedding for response {response_id}")
            return False
        
        # Update the database
        update_data = {
            "thematic_tags": thematic_tags,
            "embedding": embedding_vector,
            "tag_confidence": confidence_score
        }
        
        result = supabase.table("responses").update(update_data).eq("response_id", response_id).execute()
        
        if result.data:
            logger.info(f"Successfully enriched response {response_id}")
            return True
        else:
            logger.error(f"Failed to update response {response_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error enriching response {response_data.get('response_id', 'unknown')}: {str(e)}")
        return False

async def enrich_all_responses(batch_size: int = 10):
    """
    Enrich all responses in the database with embeddings and thematic tags.
    """
    try:
        # Get all responses that need enrichment (no embedding or thematic_tags)
        logger.info("Fetching responses that need enrichment...")
        
        result = supabase.table("responses").select("""
            response_id,
            response_value,
            thematic_tags,
            embedding,
            questions(question_text)
        """).is_("embedding", "null").execute()
        
        responses_to_enrich = result.data
        total_responses = len(responses_to_enrich)
        
        if total_responses == 0:
            logger.info("No responses need enrichment. All responses are already processed.")
            return
        
        logger.info(f"Found {total_responses} responses to enrich")
        
        # Process in batches
        successful = 0
        failed = 0
        
        for i in range(0, total_responses, batch_size):
            batch = responses_to_enrich[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_responses + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = []
            for response_data in batch:
                # Flatten the nested question data
                if response_data.get("questions"):
                    response_data["question_text"] = response_data["questions"]["question_text"]
                
                tasks.append(enrich_single_response(response_data))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    logger.error(f"Batch processing error: {result}")
                elif result:
                    successful += 1
                else:
                    failed += 1
            
            # Small delay between batches to avoid rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"Enrichment complete: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Error in enrich_all_responses: {str(e)}")

async def verify_enrichment():
    """
    Verify that the enrichment process worked correctly.
    """
    try:
        # Count total responses
        total_result = supabase.table("responses").select("response_id", count="exact").execute()
        total_count = total_result.count
        
        # Count enriched responses
        enriched_result = supabase.table("responses").select("response_id", count="exact").not_.is_("embedding", "null").execute()
        enriched_count = enriched_result.count
        
        logger.info(f"Enrichment verification:")
        logger.info(f"Total responses: {total_count}")
        logger.info(f"Enriched responses: {enriched_count}")
        logger.info(f"Coverage: {(enriched_count/total_count)*100:.1f}%")
        
        # Sample a few enriched responses
        sample_result = supabase.table("responses").select("response_id, thematic_tags, response_value").not_.is_("embedding", "null").limit(3).execute()
        
        logger.info("Sample enriched responses:")
        for sample in sample_result.data:
            logger.info(f"Response {sample['response_id']}: {sample['thematic_tags']}")
            logger.info(f"Text: {sample['response_value'][:100]}...")
            
    except Exception as e:
        logger.error(f"Error in verification: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Impact Intelligence Platform - Data Enrichment")
    print("=" * 50)
    
    async def main():
        print("Starting data enrichment process...")
        await enrich_all_responses()
        
        print("\nVerifying enrichment results...")
        await verify_enrichment()
        
        print("\n✅ Data enrichment complete!")
        print("Your responses now have embeddings and thematic tags for enhanced search.")
    
    asyncio.run(main())