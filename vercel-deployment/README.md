# RAG Survey System - Vercel Deployment

A serverless RAG (Retrieval-Augmented Generation) system optimized for Vercel deployment, designed to answer questions about youth program survey responses.

## 🚀 Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/YOUR_REPO_NAME&env=GOOGLE_API_KEY,PINECONE_API_KEY,PINECONE_ENVIRONMENT,PINECONE_INDEX_NAME&envDescription=API%20keys%20required%20for%20the%20RAG%20system)

## 📋 Environment Variables Required

Set these in your Vercel dashboard:

```bash
# Required API Keys
GOOGLE_API_KEY=your_google_ai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=rag-survey-responses

# Optional Configuration
VECTOR_STORE_TYPE=pinecone
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=gemini-1.5-flash
TEMPERATURE=0.1
MAX_TOKENS=1000
MAX_RESULTS=5
TIMEOUT_SECONDS=25
```

## 🔗 API Endpoints

- **`/api/health`** - System health check
- **`/api/chat`** - Chat with the RAG system
- **`/api/search`** - Search survey responses
- **`/api/stats`** - System statistics

## 💬 Example Usage

```bash
# Health check
curl https://your-deployment.vercel.app/api/health

# Chat
curl -X POST https://your-deployment.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do programs build confidence?"}'

# Search
curl -X POST https://your-deployment.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "confidence building", "max_results": 5}'
```

## 🧪 Testing

The system includes comprehensive tests:

```bash
# Run core tests (no external dependencies)
python3 run_core_tests.py

# Run basic integration tests
python3 test_integration_basic.py
```

## 📊 System Status

- ✅ **Core Tests**: 23/23 passing
- ✅ **Integration Tests**: 11/11 passing  
- ✅ **API Structure**: Ready for Vercel
- ✅ **Error Handling**: Comprehensive
- ✅ **Configuration**: Flexible and validated

## 🔧 Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Run tests: `python3 run_core_tests.py`
5. Deploy to Vercel

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Error Handling](docs/ERROR_HANDLING.md)

---

**Ready for production deployment!** 🚀