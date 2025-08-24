# 🎯 Advanced RAG System - Impact Intelligence Platform

This is a **production-ready advanced RAG system** that transforms youth program survey data into actionable insights through conversational AI. What started as an experiment has evolved into a complete impact intelligence platform.

## 🚀 What This System Does

- **Semantic Search**: Finds relevant survey responses by meaning, not just keywords
- **Conversational AI**: Natural language chat interface about program effectiveness  
- **Evidence-Based Insights**: Every answer backed by specific survey responses
- **Mixed Data Synthesis**: Combines MCQ responses with story narratives
- **Web Interface**: Modern chat interface at http://localhost:8002
- **Professional APIs**: REST endpoints for system integration

## Structure
- `data_sync.py` - Safe data synchronization for testing
- `langchain_rag.py` - Main Langchain RAG implementation
- `vector_store.py` - Vector database setup and management
- `embeddings_test.py` - Test embedding generation and similarity
- `advanced_server.py` - FastAPI server with advanced features
- `requirements_advanced.txt` - Specific dependencies for advanced features
- `test_advanced.py` - Comprehensive testing suite
- `benchmark_comparison.py` - Objective performance comparison framework
- `setup_advanced.py` - Automated setup script

## Approach
1. **Data Synchronization**: Create experimental database snapshot to test with realistic data without risking production
2. Start with minimal Langchain setup
3. Add vector embeddings step by step
4. Test each component independently
5. Build up to full advanced RAG system
6. Compare results with simple system using objective metrics

## Quick Start

Run the automated setup:
```bash
cd advanced_rag
python setup_advanced.py
```

Or step by step:
```bash
# 1. Install dependencies
pip install -r requirements_advanced.txt

# 2. Sync data safely
python data_sync.py

# 3. Test embeddings
python embeddings_test.py

# 4. Setup vector store
python vector_store.py

# 5. Test Langchain RAG
python langchain_rag.py

# 6. Run comprehensive tests
python test_advanced.py

# 7. Start advanced server
python advanced_server.py

# 8. Run objective benchmark
python benchmark_comparison.py
```

## Key Features

### Data Safety
- Creates isolated snapshots of production data
- No risk to existing working system
- Test subsets for rapid iteration

### Semantic Search
- Vector embeddings with sentence-transformers
- ChromaDB for efficient similarity search
- Semantic query understanding

### Objective Comparison
- Accuracy metrics (theme coverage, evidence relevance)
- Robustness metrics (error handling, response consistency)
- Latency metrics (response time, throughput)
- Clear recommendations based on results

### Production Ready
- FastAPI server on port 8001
- Health checks and error handling
- System comparison endpoints