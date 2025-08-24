from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from rag_logic import find_evidence_for_query
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Impact Intelligence Platform",
    description="API for querying social impact data with natural language",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str
    
class SourceEvidence(BaseModel):
    response_id: int
    story_text: str
    charity_name: str
    participant_demographics: str

class QueryResponse(BaseModel):
    answer: str
    evidence_count: int
    source_evidence: List[SourceEvidence]

@app.post("/search", response_model=QueryResponse)
async def search_impact_data(request: QueryRequest):
    """
    Search social impact data using natural language queries.
    Returns synthesized, evidence-backed answers.
    """
    try:
        logger.info(f"Processing query: {request.question}")
        
        # Get evidence and synthesized answer from RAG system
        evidence_docs, synthesized_answer = await find_evidence_for_query(request.question)
        
        # Format source evidence for response
        source_evidence = []
        for doc in evidence_docs[:5]:  # Limit to top 5 sources
            metadata = doc.metadata
            demographics = f"{metadata.get('age_group', 'Unknown')} {metadata.get('gender', 'participant')}"
            
            source_evidence.append(SourceEvidence(
                response_id=metadata.get('response_id', 0),
                story_text=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                charity_name=metadata.get('charity_name', 'Unknown'),
                participant_demographics=demographics
            ))
        
        return QueryResponse(
            answer=synthesized_answer,
            evidence_count=len(evidence_docs),
            source_evidence=source_evidence
        )
        
    except Exception as e:
        # Log detailed error for system improvement
        error_details = {
            "query": request.question,
            "error": str(e),
            "error_type": type(e).__name__
        }
        logger.error(f"Query processing failed: {error_details}")
        
        # Store error for QA review (optional - implement if needed)
        # await log_query_error(error_details)
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Impact Intelligence Platform"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)