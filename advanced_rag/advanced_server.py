"""
Advanced FastAPI server with Langchain RAG capabilities
"""
import os
import sys
sys.path.append('..')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
from langchain_rag import AdvancedRAGSystem

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Impact Intelligence Platform",
    description="Advanced RAG system with semantic search and Langchain integration",
    version="2.0.0"
)

# Global RAG system instance
rag_system = None

class QueryRequest(BaseModel):
    query: str
    max_results: int = 5

class QueryResponse(BaseModel):
    question: str
    answer: str
    evidence_count: int
    source_documents: List[Dict[str, Any]]
    system_type: str

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    global rag_system
    try:
        print("🚀 Initializing Advanced RAG System...")
        rag_system = AdvancedRAGSystem()
        print("✅ Advanced RAG System ready!")
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {str(e)}")
        print("💡 Make sure vector store is populated: python vector_store.py")

@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "message": "Advanced Impact Intelligence Platform",
        "version": "2.0.0",
        "features": [
            "Semantic search with vector embeddings",
            "Langchain integration",
            "Advanced query understanding",
            "Evidence-based insights"
        ],
        "status": "ready" if rag_system else "initializing"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    return {
        "status": "healthy",
        "system": "advanced_langchain_rag",
        "vector_store": "connected"
    }

@app.post("/search", response_model=QueryResponse)
async def search_query(request: QueryRequest):
    """Process search query using advanced RAG"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        result = rag_system.query(request.query)
        
        return QueryResponse(
            question=result['question'],
            answer=result['answer'],
            evidence_count=result['evidence_count'],
            source_documents=result['source_documents'],
            system_type=result['system_type']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/compare")
async def compare_systems(request: QueryRequest):
    """Compare advanced and simple RAG systems"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        comparison = rag_system.compare_with_simple_system(request.query)
        
        if comparison is None:
            raise HTTPException(status_code=500, detail="Comparison failed")
        
        return {
            "query": comparison['query'],
            "advanced_system": {
                "answer": comparison['advanced']['answer'],
                "evidence_count": comparison['advanced']['evidence_count'],
                "system_type": comparison['advanced']['system_type']
            },
            "simple_system": {
                "answer": comparison['simple']['answer'],
                "evidence_count": comparison['simple']['evidence_count'],
                "system_type": comparison['simple'].get('system_type', 'simple_rag')
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Get vector store stats
        doc_count = rag_system.vectorstore._collection.count()
        
        return {
            "vector_store": {
                "total_documents": doc_count,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "vector_dimension": 384
            },
            "llm": {
                "model": "gemini-1.5-flash",
                "provider": "Google AI"
            },
            "capabilities": [
                "Semantic similarity search",
                "Context-aware responses",
                "Multi-document synthesis",
                "Evidence attribution"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Advanced Impact Intelligence Platform Server")
    print("=" * 60)
    print("Features:")
    print("• Semantic search with vector embeddings")
    print("• Langchain integration")
    print("• Advanced query understanding")
    print("• System comparison capabilities")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Different port from simple system
        reload=True
    )