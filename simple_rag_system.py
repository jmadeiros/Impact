"""
Simplified RAG system that bypasses compatibility issues.
Uses direct HTTP requests and Google AI API.
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from config import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

class SimpleRAGSystem:
    def __init__(self):
        self.supabase_headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        self.google_api_key = GOOGLE_API_KEY
    
    def query_supabase(self, table: str, params: str = "") -> List[Dict]:
        """Query Supabase table via REST API."""
        try:
            url = f"{SUPABASE_URL}/rest/v1/{table}{params}"
            response = requests.get(url, headers=self.supabase_headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Supabase query failed: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error querying Supabase: {str(e)}")
            return []
    
    def call_google_ai(self, prompt: str) -> str:
        """Call Google AI API directly."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.google_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "No response generated"
            else:
                logger.error(f"Google AI API failed: {response.status_code} - {response.text}")
                return f"Error calling Google AI: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error calling Google AI: {str(e)}")
            return f"Error: {str(e)}"
    
    def extract_search_parameters(self, user_question: str) -> Dict[str, Any]:
        """Use Google AI to extract search parameters from user question."""
        
        # Get contextual questions for context
        questions = self.query_supabase("questions", "?outcome_measured=eq.contextual")
        
        contextual_desc = "\n".join([
            f"- {q['question_id']}: {q['question_text']}"
            for q in questions
        ])
        
        prompt = f"""
Analyze this user question and extract search parameters: "{user_question}"

Available contextual questions in our database:
{contextual_desc}

Extract the following parameters and return as JSON:
- charity_name: specific organization name if mentioned (e.g., "YCUK", "Palace for Life", "Symphony Studios")
- age_group: age range if mentioned (e.g., "12-14", "15-17", "18+")
- gender: if specified (e.g., "Male", "Female")
- themes: key themes/concepts for searching (e.g., ["resilience", "creative", "leadership"])

Examples:
- "How do YCUK programs help teenage girls?" → {{"charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "themes": ["programs", "help"]}}
- "Show me stories about resilience" → {{"themes": ["resilience", "stories", "overcoming"]}}

Return only valid JSON:
"""
        
        response = self.call_google_ai(prompt)
        
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: basic keyword extraction
        return {
            "themes": [user_question.lower()],
            "charity_name": None,
            "age_group": None,
            "gender": None
        }
    
    def search_responses(self, search_params: Dict[str, Any]) -> List[Dict]:
        """Search responses based on extracted parameters."""
        
        # Build query parameters
        query_parts = []
        
        if search_params.get("charity_name"):
            query_parts.append(f"charity_name=eq.{search_params['charity_name']}")
        
        if search_params.get("age_group"):
            query_parts.append(f"age_group=eq.{search_params['age_group']}")
            
        if search_params.get("gender"):
            query_parts.append(f"gender=eq.{search_params['gender']}")
        
        # Query responses without join first
        query_params = "?select=*"
        if query_parts:
            query_params += "&" + "&".join(query_parts)
        
        # Limit results
        query_params += "&limit=20"
        
        responses = self.query_supabase("responses", query_params)
        
        # Get questions separately and merge
        questions = self.query_supabase("questions")
        questions_dict = {q['question_id']: q for q in questions}
        
        # Add question info to responses
        for response in responses:
            question_id = response.get('question_id')
            if question_id in questions_dict:
                response['questions'] = questions_dict[question_id]
        
        # If we have themes, do basic text filtering
        if search_params.get("themes"):
            themes = search_params["themes"]
            filtered_responses = []
            
            for response in responses:
                response_text = response.get("response_value", "").lower()
                question_text = ""
                if response.get("questions"):
                    question_text = response["questions"].get("question_text", "").lower()
                
                # Check if any theme appears in response or question
                for theme in themes:
                    if theme.lower() in response_text or theme.lower() in question_text:
                        filtered_responses.append(response)
                        break
            
            if filtered_responses:
                responses = filtered_responses
        
        return responses[:10]  # Limit to top 10
    
    def synthesize_answer(self, user_question: str, responses: List[Dict]) -> str:
        """Generate final answer using Google AI."""
        
        if not responses:
            return "I couldn't find sufficient evidence to answer your question. Please try rephrasing or being more specific."
        
        # Prepare evidence context
        evidence_context = ""
        for i, response in enumerate(responses[:5]):  # Limit to top 5
            evidence_context += f"""
Evidence {i+1}:
Response: "{response['response_value']}"
Participant: {response.get('age_group', 'Unknown')} {response.get('gender', 'participant')}
Organization: {response.get('charity_name', 'Unknown')}
Question: {response.get('questions', {}).get('question_text', 'N/A')}
---
"""
        
        synthesis_prompt = f"""
You are an expert analyst synthesizing social impact data for funders and stakeholders.

USER QUESTION: {user_question}

EVIDENCE ({len(responses)} total responses):
{evidence_context}

Please provide a comprehensive answer following the "Quantify, then Qualify" protocol:

1. QUANTIFY: Start with key statistics and numbers from the evidence
   - How many responses support the findings?
   - What demographic patterns emerge?
   - Any measurable outcomes or trends?

2. QUALIFY: Provide rich qualitative insights
   - Include 2-3 direct quotes as evidence
   - Explain the deeper meaning and implications
   - Address nuances and context

3. CONCLUSION: Synthesize into actionable insights for funders

Format your response as a professional briefing that demonstrates clear impact and evidence-based conclusions.
"""
        
        return self.call_google_ai(synthesis_prompt)
    
    def process_query(self, user_question: str) -> Dict[str, Any]:
        """Main function to process a user query end-to-end."""
        
        logger.info(f"Processing query: {user_question}")
        
        # Step 1: Extract search parameters
        search_params = self.extract_search_parameters(user_question)
        logger.info(f"Extracted parameters: {search_params}")
        
        # Step 2: Search for relevant responses
        responses = self.search_responses(search_params)
        logger.info(f"Found {len(responses)} relevant responses")
        
        # Step 3: Synthesize answer
        answer = self.synthesize_answer(user_question, responses)
        
        # Step 4: Format source evidence
        source_evidence = []
        for response in responses[:5]:
            demographics = f"{response.get('age_group', 'Unknown')} {response.get('gender', 'participant')}"
            source_evidence.append({
                "response_id": response.get("response_id", 0),
                "story_text": response.get("response_value", "")[:200] + "..." if len(response.get("response_value", "")) > 200 else response.get("response_value", ""),
                "charity_name": response.get("charity_name", "Unknown"),
                "participant_demographics": demographics
            })
        
        return {
            "answer": answer,
            "evidence_count": len(responses),
            "source_evidence": source_evidence
        }

def test_system():
    """Test the RAG system with sample queries."""
    
    print("Impact Intelligence Platform - Simple RAG Test")
    print("=" * 60)
    
    rag = SimpleRAGSystem()
    
    test_queries = [
        "How do creative programs build resilience?",
        "What impact does Palace for Life have?",
        "Show me stories about overcoming challenges"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 40)
        
        result = rag.process_query(query)
        
        print(f"📊 Evidence Count: {result['evidence_count']}")
        print(f"📝 Answer: {result['answer'][:200]}...")
        
        if result['source_evidence']:
            print(f"💬 Sample Quote: \"{result['source_evidence'][0]['story_text']}\"")
        
        print()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_system()