"""
Core RAG logic for the simple system
Migrated from rag_logic.py with updated imports
"""
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.tools import Tool
from langchain.schema import Document
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from supabase import create_client, Client
import json
import logging

# Updated import path
from impact.shared.config.base import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize LLM and embeddings
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.1
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

# Initialize vector store
vector_store = SupabaseVectorStore(
    client=supabase,
    embedding=embeddings,
    table_name="responses",
    query_name="match_responses"
)

async def get_contextual_questions() -> List[Dict[str, Any]]:
    """
    Fetch contextual questions from Supabase to use in tool definition.
    These serve as our 'ground truth' proxy questions.
    """
    try:
        response = supabase.table("questions").select("*").eq("outcome_measured", "contextual").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching contextual questions: {str(e)}")
        return []

class SearchParameters(BaseModel):
    """Structured parameters for database search."""
    charity_name: Optional[str] = Field(None, description="Filter by specific charity/organization")
    age_group: Optional[str] = Field(None, description="Filter by participant age group")
    gender: Optional[str] = Field(None, description="Filter by participant gender")
    question_ids: Optional[List[str]] = Field(None, description="List of specific question IDs to focus on")
    thematic_query: Optional[str] = Field(None, description="Core concept/theme to search for (used for semantic similarity)")

async def create_search_tool_schema() -> Dict[str, Any]:
    """
    Create a tool schema for LLM function calling.
    Dynamically includes contextual questions in the description.
    """
    contextual_questions = await get_contextual_questions()
    
    # Build dynamic description including contextual questions
    contextual_desc = "\n".join([
        f"- {q['question_id']}: {q['question_text']}" + 
        (f" (Options: {q['mcq_options']})" if q['mcq_options'] else "")
        for q in contextual_questions
    ])
    
    tool_schema = {
        "name": "search_database",
        "description": f"""
Search the social impact database with structured filters.

Available contextual outcome questions:
{contextual_desc}

Use this tool to extract search parameters from the user's natural language query.
Focus on identifying relevant demographic filters and thematic concepts.
""",
        "parameters": SearchParameters.model_json_schema()
    }
    
    return tool_schema

async def execute_hybrid_search(search_params: SearchParameters) -> List[Document]:
    """
    Execute unified hybrid search using Langchain's SupabaseVectorStore.
    Always uses similarity_search with metadata filtering for consistent behavior.
    """
    try:
        # Build metadata filter
        metadata_filter = {}
        if search_params.charity_name:
            metadata_filter["charity_name"] = search_params.charity_name
        if search_params.age_group:
            metadata_filter["age_group"] = search_params.age_group
        if search_params.gender:
            metadata_filter["gender"] = search_params.gender
        if search_params.question_ids and len(search_params.question_ids) > 0:
            # For multiple question IDs, take the first one
            # TODO: Enhance to handle multiple question IDs with OR logic
            metadata_filter["question_id"] = search_params.question_ids[0]
        
        # Use thematic_query or empty string for unified search path
        query_text = search_params.thematic_query or ""
        
        # Always use vector store similarity search - it handles both cases:
        # 1. With thematic_query: true semantic similarity search
        # 2. Without thematic_query: filtered results with default ordering
        documents = vector_store.similarity_search(
            query=query_text,
            k=20,  # Retrieve top 20 most relevant
            filter=metadata_filter if metadata_filter else None
        )
        
        logger.info(f"Retrieved {len(documents)} documents from hybrid search")
        logger.info(f"Search params: {search_params.model_dump()}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error in hybrid search: {str(e)}")
        # Fallback to direct database query if vector search fails
        try:
            logger.info("Attempting fallback to direct database query")
            query = supabase.table("responses").select("*, questions(*)")
            
            if search_params.charity_name:
                query = query.eq("charity_name", search_params.charity_name)
            if search_params.age_group:
                query = query.eq("age_group", search_params.age_group)
            if search_params.gender:
                query = query.eq("gender", search_params.gender)
            if search_params.question_ids and len(search_params.question_ids) > 0:
                query = query.eq("question_id", search_params.question_ids[0])
                
            response = query.limit(20).execute()
            
            documents = []
            for row in response.data:
                doc = Document(
                    page_content=row["response_value"],
                    metadata={
                        "response_id": row["response_id"],
                        "participant_id": row["participant_id"],
                        "charity_name": row["charity_name"],
                        "age_group": row["age_group"],
                        "gender": row["gender"],
                        "question_id": row["question_id"],
                        "question_text": row["questions"]["question_text"] if row["questions"] else None,
                        "thematic_tags": row.get("thematic_tags", [])
                    }
                )
                documents.append(doc)
            
            logger.info(f"Fallback query retrieved {len(documents)} documents")
            return documents
            
        except Exception as fallback_error:
            logger.error(f"Fallback query also failed: {str(fallback_error)}")
            return []

async def deconstruct_query_with_llm(user_question: str) -> SearchParameters:
    """
    Use LLM with direct function calling to deconstruct user query into structured parameters.
    Modern approach using .bind() for more reliable function calling.
    """
    try:
        # Get the tool schema
        tool_schema = await create_search_tool_schema()
        
        # Bind the tool to the LLM for function calling
        llm_with_tools = llm.bind(functions=[tool_schema])
        
        prompt = f"""
Analyze this user question and extract structured search parameters: "{user_question}"

Focus on identifying:
- Relevant demographic filters (age_group, gender, charity_name)
- Specific outcome questions that relate to the query  
- Core thematic concepts for semantic search

Extract the parameters that would help find the most relevant survey responses.

Examples:
- "How do creative programs help teenage girls?" → age_group: "16-18", gender: "female", thematic_query: "creative programs resilience confidence"
- "What impact does YCUK have on leadership?" → charity_name: "YCUK", thematic_query: "leadership development skills"
- "Show me stories about overcoming challenges" → thematic_query: "overcoming challenges resilience growth"
"""
        
        # Invoke the LLM with function calling
        response = llm_with_tools.invoke(prompt)
        
        # Extract function call arguments
        if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
            function_call = response.additional_kwargs['function_call']
            if function_call['name'] == 'search_database':
                arguments = json.loads(function_call['arguments'])
                return SearchParameters(**arguments)
        
        # Fallback: try to parse from response content
        if hasattr(response, 'content'):
            try:
                # Look for JSON in the response
                content = response.content
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    arguments = json.loads(json_str)
                    return SearchParameters(**arguments)
            except:
                pass
        
        # Final fallback: basic thematic query
        logger.warning(f"Could not extract structured parameters, using basic thematic query")
        return SearchParameters(thematic_query=user_question)
            
    except Exception as e:
        logger.error(f"Error in query deconstruction: {str(e)}")
        return SearchParameters(thematic_query=user_question)

async def synthesize_final_answer(user_question: str, evidence_docs: List[Document]) -> str:
    """
    Implement the "Quantify, then Qualify" protocol for final answer synthesis.
    """
    if not evidence_docs:
        return "I couldn't find sufficient evidence to answer your question. Please try rephrasing or being more specific."
    
    # Prepare evidence context
    evidence_context = ""
    for i, doc in enumerate(evidence_docs[:10]):  # Limit to top 10 for context window
        metadata = doc.metadata
        evidence_context += f"""
Evidence {i+1}:
Response: "{doc.page_content}"
Participant: {metadata.get('age_group', 'Unknown')} year old {metadata.get('gender', 'participant')}
Organization: {metadata.get('charity_name', 'Unknown')}
Question Context: {metadata.get('question_text', 'N/A')}
---
"""
    
    synthesis_prompt = PromptTemplate(
        input_variables=["user_question", "evidence_context", "evidence_count"],
        template="""
You are an expert analyst synthesizing social impact data for funders and stakeholders.

USER QUESTION: {user_question}

EVIDENCE ({evidence_count} total responses):
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
    )
    
    try:
        formatted_prompt = synthesis_prompt.format(
            user_question=user_question,
            evidence_context=evidence_context,
            evidence_count=len(evidence_docs)
        )
        
        response = llm.invoke(formatted_prompt)
        return response.content
        
    except Exception as e:
        logger.error(f"Error in synthesis: {str(e)}")
        return f"Based on {len(evidence_docs)} pieces of evidence, I found relevant information about your query, but encountered an error in synthesis. Please try again."

async def find_evidence_for_query(user_question: str) -> tuple[List[Document], str]:
    """
    Main RAG function that processes a user question and returns evidence + synthesized answer.
    
    Steps:
    A. Query Deconstruction via Direct Function Calling
    B. Unified Hybrid Search Execution 
    C. Evidence Synthesis
    """
    try:
        logger.info(f"Processing user question: {user_question}")
        
        # Step A: Query Deconstruction using modern .bind() approach
        search_params = await deconstruct_query_with_llm(user_question)
        logger.info(f"Extracted search parameters: {search_params.model_dump()}")
        
        # Step B: Execute Unified Hybrid Search
        evidence_documents = await execute_hybrid_search(search_params)
        
        # Step C: Synthesize Final Answer
        synthesized_answer = await synthesize_final_answer(user_question, evidence_documents)
        
        return evidence_documents, synthesized_answer
        
    except Exception as e:
        logger.error(f"Error in find_evidence_for_query: {str(e)}")
        return [], f"I encountered an error processing your query: {str(e)}"