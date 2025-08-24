"""
Working FastAPI server using the simplified RAG system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from simple_rag_system import SimpleRAGSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Impact Intelligence Platform",
    description="API for querying social impact data with natural language",
    version="1.0.0"
)

# Initialize RAG system
rag_system = SimpleRAGSystem()

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
        
        # Process query through RAG system
        result = rag_system.process_query(request.question)
        
        # Format source evidence
        source_evidence = []
        for evidence in result['source_evidence']:
            source_evidence.append(SourceEvidence(
                response_id=evidence['response_id'],
                story_text=evidence['story_text'],
                charity_name=evidence['charity_name'],
                participant_demographics=evidence['participant_demographics']
            ))
        
        return QueryResponse(
            answer=result['answer'],
            evidence_count=result['evidence_count'],
            source_evidence=source_evidence
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Impact Intelligence Platform"}

@app.get("/")
async def root():
    """Root endpoint with usage instructions"""
    return {
        "message": "Impact Intelligence Platform API",
        "usage": "POST /search with {'question': 'your question here'}",
        "examples": [
            "How do creative programs build resilience?",
            "What impact does Palace for Life have?",
            "Show me stories about overcoming challenges"
        ],
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Impact Intelligence Platform")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print()
    print("Sample queries:")
    print('- "How do creative programs build resilience?"')
    print('- "What impact does Palace for Life have?"')
    print('- "Show me stories about overcoming challenges"')
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)