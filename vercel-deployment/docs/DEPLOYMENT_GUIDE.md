# Vercel RAG System Deployment Guide

## Overview

This comprehensive guide provides step-by-step instructions for deploying the Advanced RAG System to Vercel. The system includes serverless API endpoints, external vector storage (Pinecone/Supabase), comprehensive error handling, and user-friendly responses.

This guide covers both fresh deployments and deployments with existing data, providing complete instructions for all scenarios.

## Prerequisites

### Required Accounts and Services

1. **Vercel Account**
   - Sign up at [vercel.com](https://vercel.com)
   - Install Vercel CLI: `npm install -g vercel`

2. **Google Cloud Platform**
   - Create a project and enable the Generative AI API
   - Generate an API key for Gemini models

3. **Pinecone Account** (Primary Vector Store)
   - Sign up at [pinecone.io](https://pinecone.io)
   - Create a new index with 384 dimensions
   - Note your API key and environment

4. **Supabase Account** (Fallback Vector Store)
   - Sign up at [supabase.com](https://supabase.com)
   - Create a new project
   - Enable the pgvector extension

### Local Development Setup

1. **Clone and Setup**
   ```bash
   git clone <your-repository>
   cd vercel-deployment
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see configuration section)
   ```

## Configuration

### Environment Variables

Create a `.env` file in the `vercel-deployment` directory with the following variables:

```bash
# Required API Keys
GOOGLE_API_KEY=your_google_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Pinecone Configuration (Primary Vector Store)
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=rag-survey-responses
PINECONE_NAMESPACE=production

# Supabase Configuration (Fallback Vector Store)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key

# Model Configuration
VECTOR_STORE_TYPE=pinecone
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=gemini-1.5-flash
TEMPERATURE=0.1
MAX_TOKENS=1000
MAX_RESULTS=5

# Serverless Configuration
TIMEOUT_SECONDS=25
MAX_RETRIES=3
MEMORY_WARNING_THRESHOLD=0.8
DEBUG=false

# Error Handling Configuration
INCLUDE_TECHNICAL_DETAILS=false
INCLUDE_CONTACT_INFO=true
SUPPORT_EMAIL=support@yourorganization.com
SERVICE_NAME=Youth Program Insights
MAX_SUGGESTION_COUNT=3
INCLUDE_RETRY_INFO=true

# Rate Limiting
RATE_LIMIT_WINDOW=60
MAX_REQUESTS_PER_WINDOW=100
```

### API Key Setup

#### Google API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable the "Generative Language API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Restrict the key to the Generative Language API

#### Pinecone API Key
1. Log in to [Pinecone Console](https://app.pinecone.io)
2. Go to "API Keys" in the sidebar
3. Create a new API key
4. Note your environment (e.g., `gcp-starter`, `us-west1-gcp`)

#### Supabase Configuration
1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings → API
4. Copy the "URL" and "service_role" key (not anon key)

### Vector Store Setup

#### Pinecone Index Creation
1. In Pinecone Console, click "Create Index"
2. **Index Name**: `rag-survey-responses`
3. **Dimensions**: `384` (for all-MiniLM-L6-v2 embeddings)
4. **Metric**: `cosine`
5. **Environment**: Select your environment
6. Click "Create Index"

#### Supabase Vector Setup (Optional Fallback)
1. In Supabase SQL Editor, run:
   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;
   
   -- Create vector documents table
   CREATE TABLE vector_documents (
     id TEXT PRIMARY KEY,
     text TEXT NOT NULL,
     embedding vector(384),
     charity_name TEXT,
     age_group TEXT,
     gender TEXT,
     question_text TEXT,
     question_type TEXT,
     response_length INTEGER,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Create index for vector similarity search
   CREATE INDEX ON vector_documents USING ivfflat (embedding vector_cosine_ops);
   ```

## Data Migration

### Export from ChromaDB (If Applicable)

If you have existing data in ChromaDB, export it first:

```bash
cd vercel-deployment
python3 scripts/export_chromadb.py
```

This creates `chromadb_export.json` with all your documents and embeddings.

### Import to Pinecone

```bash
python3 scripts/migrate_to_pinecone.py
```

This script will:
- Read the ChromaDB export (or create new embeddings)
- Upload to your Pinecone index
- Validate the migration
- Show progress and statistics

### Verify Migration

```bash
python3 test_env_loading.py
```

This will test your environment setup and vector store connections.

## Local Testing

### Test Individual Components

```bash
# Test environment loading
python3 test_env_loading.py

# Test error handling system
python3 test_error_handling.py

# Test user-friendly error responses
python3 test_user_friendly_errors.py

# Test overall system structure
python3 test_structure.py
```

Expected output:
```
✅ Environment variables loaded correctly
✅ Vector store connection successful
✅ LLM responding correctly
✅ Error handling functional
✅ User-friendly responses working
✅ All API endpoints structured correctly
✅ Ready for deployment
```

### Test API Endpoints Locally

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Run local development server
vercel dev
```

This starts a local server at `http://localhost:3000` where you can test:
- `POST /api/search` - Search functionality
- `POST /api/chat` - Conversational interface
- `GET /api/health` - Health checks
- `GET /api/stats` - System statistics

### Example API Requests

#### Search Request
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do programs build confidence?",
    "max_results": 5,
    "filters": {
      "age_group": ["13-15", "16-18"]
    }
  }'
```

#### Chat Request
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the benefits of youth programs?",
    "session_id": "user_123",
    "include_context": true
  }'
```

#### Health Check
```bash
curl http://localhost:3000/api/health?detailed=true
```

## Vercel Deployment

### Project Setup

1. **Login to Vercel**
   ```bash
   vercel login
   ```

2. **Initialize Vercel Project**
   ```bash
   # In vercel-deployment directory
   vercel
   ```
   
   Follow the prompts:
   - Link to existing project or create new
   - Choose your team/account
   - Project name: `advanced-rag-system` (or your preferred name)
   - Directory: `./`
   - Override settings: No (unless you need custom settings)

3. **Configure Build Settings**
   
   Ensure your `vercel.json` is properly configured:
   ```json
   {
     "functions": {
       "api/*.py": {
         "runtime": "python3.9",
         "maxDuration": 25,
         "memory": 1024
       }
     },
     "build": {
       "env": {
         "PYTHONPATH": "./lib"
       }
     }
   }
   ```

### Environment Variables in Vercel

#### Option A: Via Vercel CLI (Recommended)
```bash
# Required API Keys
vercel env add GOOGLE_API_KEY
vercel env add PINECONE_API_KEY

# Pinecone Configuration
vercel env add PINECONE_ENVIRONMENT
vercel env add PINECONE_INDEX_NAME
vercel env add PINECONE_NAMESPACE

# Supabase Configuration (if using)
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Model Configuration
vercel env add VECTOR_STORE_TYPE
vercel env add EMBEDDING_MODEL
vercel env add LLM_MODEL
vercel env add TEMPERATURE
vercel env add MAX_TOKENS
vercel env add MAX_RESULTS

# Serverless Configuration
vercel env add TIMEOUT_SECONDS
vercel env add MAX_RETRIES
vercel env add MEMORY_WARNING_THRESHOLD
vercel env add DEBUG

# Error Handling Configuration
vercel env add INCLUDE_TECHNICAL_DETAILS
vercel env add INCLUDE_CONTACT_INFO
vercel env add SUPPORT_EMAIL
vercel env add SERVICE_NAME
vercel env add MAX_SUGGESTION_COUNT
vercel env add INCLUDE_RETRY_INFO

# Rate Limiting
vercel env add RATE_LIMIT_WINDOW
vercel env add MAX_REQUESTS_PER_WINDOW
```

#### Option B: Via Vercel Dashboard
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to Settings → Environment Variables
4. Add each variable from your `.env` file
5. Set appropriate environments (Production, Preview, Development)

#### Option C: Bulk Import
```bash
# Import from .env file (be careful with sensitive data)
vercel env pull .env.vercel
# Edit .env.vercel to remove sensitive info, then:
# Manually add variables via CLI or dashboard
```

### Deploy to Preview

```bash
# Deploy to preview environment first
vercel --prod=false
```

This creates a preview URL like: `https://advanced-rag-system-abc123.vercel.app`

### Test Preview Deployment

```bash
# Test health endpoint
curl https://your-preview-url.vercel.app/api/health?detailed=true

# Test search endpoint
curl -X POST https://your-preview-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do programs build confidence?",
    "max_results": 3
  }'

# Test chat endpoint
curl -X POST https://your-preview-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about youth programs",
    "session_id": "test_session"
  }'

# Test error handling
curl -X POST https://your-preview-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Deploy to Production

Once preview testing is successful:

```bash
# Deploy to production
vercel --prod
```

### Configure Custom Domain (Optional)

1. **In Vercel Dashboard:**
   - Go to Project Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

2. **Update DNS:**
   ```
   # Add CNAME record:
   # Name: api (or your subdomain)
   # Value: cname.vercel-dns.com
   ```

## Post-Deployment Validation

### Health Check Validation

```bash
curl https://your-deployment-url.vercel.app/api/health?detailed=true
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-25T15:30:45.123Z",
  "service": "Youth Program Insights",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "rag_engine": {
      "status": "healthy",
      "config": {
        "vector_store_type": "pinecone",
        "llm_model": "gemini-1.5-flash",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
      }
    },
    "vector_store": {
      "status": "healthy",
      "stats": {
        "total_vectors": 1000,
        "vector_store_type": "pinecone"
      }
    }
  },
  "response_time": 0.234
}
```

### Functional Testing

#### Test Search Functionality
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do programs help young people?",
    "max_results": 5,
    "filters": {
      "age_group": ["13-15"]
    }
  }'
```

Expected response:
```json
{
  "success": true,
  "query": "How do programs help young people?",
  "answer": "Based on survey responses from youth programs...",
  "evidence_count": 5,
  "source_documents": [...],
  "metadata": {
    "organizations": ["YCUK", "Palace for Life"],
    "age_groups": ["13-15"],
    "system_type": "serverless_rag",
    "processing_time": 2.1
  },
  "timestamp": "2025-08-25T15:30:45.123Z"
}
```

#### Test Chat Functionality
```bash
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main benefits of youth programs?",
    "session_id": "validation_test",
    "include_context": true
  }'
```

#### Test Error Handling
```bash
# Test validation error
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected user-friendly error response
{
  "success": false,
  "error": {
    "type": "validation",
    "title": "Problem with your question",
    "message": "There's an issue with your question: is required and cannot be empty",
    "suggestions": [
      "Check that your question is properly formatted",
      "Make sure your question meets the requirements",
      "Try the example format shown below"
    ],
    "example": {
      "message": "Here's an example of the correct format:",
      "data": {
        "query": "How do programs help?",
        "max_results": 5
      }
    }
  }
}
```

### Performance Testing

```bash
# Test response times
time curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits?"}'
```

Expected performance:
- **Cold start**: < 10 seconds
- **Warm requests**: < 3 seconds
- **Health check**: < 1 second

### Load Testing (Optional)

```bash
# Install Apache Bench for load testing
# macOS: brew install httpd
# Ubuntu: sudo apt-get install apache2-utils

# Test with 10 concurrent requests
ab -n 50 -c 10 -p search_payload.json -T application/json \
   https://your-deployment-url.vercel.app/api/search
```

Create `search_payload.json`:
```json
{"query": "How do programs build confidence?", "max_results": 3}
```

## Monitoring and Maintenance

### Vercel Analytics and Monitoring

1. **Enable Vercel Analytics**
   - Go to Project Settings → Analytics
   - Enable Web Analytics and Speed Insights
   - Monitor function execution times and success rates

2. **Function Logs**
   ```bash
   # View real-time logs
   vercel logs --follow
   
   # View logs for specific function
   vercel logs --follow api/search.py
   
   # View logs for specific deployment
   vercel logs <deployment-url>
   ```

3. **Performance Monitoring**
   ```bash
   # Check function performance
   vercel inspect <deployment-url>
   
   # Monitor function metrics
   curl https://your-deployment-url.vercel.app/api/stats
   ```

### External Service Monitoring

#### Pinecone Monitoring
- Monitor index usage and query volume
- Track vector count and storage usage
- Set up alerts for quota limits
- Monitor query performance and latency

#### Google AI API Monitoring
- Track API usage and quotas
- Monitor request success rates
- Set up billing alerts
- Watch for rate limit issues

#### Supabase Monitoring (if used)
- Monitor database performance
- Track storage usage
- Monitor connection pool usage
- Set up alerts for downtime

### Custom Monitoring Endpoints

The system includes built-in monitoring:

```bash
# System health and component status
curl https://your-deployment-url.vercel.app/api/health?detailed=true

# System statistics and performance metrics
curl https://your-deployment-url.vercel.app/api/stats

# Example stats response:
{
  "system_type": "serverless_rag",
  "vector_store": {
    "total_vectors": 1000,
    "vector_store_type": "pinecone",
    "index_name": "rag-survey-responses"
  },
  "config": {
    "llm_model": "gemini-1.5-flash",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "max_results": 5,
    "temperature": 0.1
  }
}
```

### Regular Maintenance Tasks

#### Daily (Automated)
- Health check monitoring
- Error rate tracking
- Performance metrics collection

#### Weekly
- Review error logs and patterns
- Monitor API usage and costs
- Check system performance trends
- Validate backup systems

#### Monthly
- Update dependencies if needed
- Review and rotate API keys
- Analyze usage patterns and optimize
- Performance tuning and optimization
- Security audit and updates

#### Quarterly
- Comprehensive system review
- Capacity planning and scaling
- Cost optimization analysis
- Disaster recovery testing

### Alerting Setup

#### Vercel Alerts
Set up alerts in Vercel dashboard for:
- Function errors exceeding threshold
- Response time degradation
- High memory usage
- Deployment failures

#### External Service Alerts
- **Pinecone**: Set up usage and performance alerts
- **Google AI**: Configure quota and billing alerts
- **Supabase**: Monitor database performance alerts

#### Custom Health Check Monitoring
```bash
# Set up external monitoring service to check:
curl https://your-deployment-url.vercel.app/api/health

# Alert if status is not "healthy" or response time > 5s
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Cold Start Timeouts
**Symptoms:** Functions timing out on first request
**Solutions:**
- Reduce `MAX_RESULTS` to lower processing time
- Implement request warming
- Optimize embedding model loading

```bash
# Test cold start performance
curl -w "@curl-format.txt" https://your-url.vercel.app/api/health
```

#### 2. Memory Limit Exceeded
**Symptoms:** Functions failing with memory errors
**Solutions:**
- Reduce batch sizes in vector operations
- Optimize data structures
- Use streaming for large responses

```bash
# Monitor memory usage
vercel logs --follow
```

#### 3. Vector Store Connection Issues
**Symptoms:** "Service temporarily unavailable" errors
**Solutions:**
- Verify API keys and environment variables
- Check service status pages
- Implement retry logic

```bash
# Test vector store connection
python -c "
from lib.vector_client import VectorStoreFactory
client = VectorStoreFactory.create_from_env()
print('Health:', client.health_check())
print('Stats:', client.get_stats())
"
```

#### 4. LLM API Rate Limits
**Symptoms:** "Too many requests" errors
**Solutions:**
- Implement request queuing
- Use different API keys for different environments
- Reduce request frequency

#### 5. Environment Variable Issues
**Symptoms:** Configuration errors on deployment
**Solutions:**
- Verify all required variables are set
- Check variable names match exactly
- Ensure proper scoping (Production/Preview/Development)

```bash
# List all environment variables
vercel env ls
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Set debug environment variable
vercel env add DEBUG
# Enter: true

# Redeploy
vercel --prod
```

This provides:
- Detailed error messages
- Stack traces
- Performance metrics
- Request/response logging

### Performance Optimization

#### 1. Function Configuration
Update `vercel.json` for better performance:

```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9",
      "maxDuration": 25,
      "memory": 1024
    }
  }
}
```

#### 2. Caching Strategy
Implement caching for frequently requested data:

```python
# In your API endpoints
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query_hash):
    # Expensive operations here
    pass
```

#### 3. Connection Pooling
Optimize database connections:

```python
# Use connection pooling for external services
# Implement in vector_client.py
```

## Security Considerations

### 1. API Key Management
- Use Vercel's encrypted environment variables
- Rotate keys regularly
- Use different keys for different environments
- Never commit keys to version control

### 2. Rate Limiting
Implement rate limiting to prevent abuse:

```python
# Add to API endpoints
from functools import wraps
import time

def rate_limit(max_requests=100, window=3600):
    # Implementation here
    pass
```

### 3. Input Validation
Ensure all inputs are properly validated:

```python
# Validate query length, format, etc.
if len(query) > 1000:
    return error_response("Query too long")
```

### 4. CORS Configuration
Configure CORS appropriately:

```python
# In API responses
headers = {
    'Access-Control-Allow-Origin': 'https://yourdomain.com',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}
```

## Cost Optimization

### 1. Vector Store Costs
- **Pinecone:** Monitor vector count and queries
- **Supabase:** Optimize database queries and storage

### 2. LLM API Costs
- Use appropriate model sizes
- Implement response caching
- Monitor token usage

### 3. Vercel Costs
- Optimize function execution time
- Monitor bandwidth usage
- Use appropriate plan tier

## Support and Resources

### Documentation
- [Vercel Python Runtime](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Google AI Documentation](https://ai.google.dev/)
- [LangChain Documentation](https://python.langchain.com/)

### Getting Help
- Check error logs in Vercel dashboard
- Review troubleshooting section above
- Contact support at: `SUPPORT_EMAIL` (configured in environment)
- Create GitHub issues for bugs or feature requests

### Useful Commands Reference

```bash
# Deployment
vercel                    # Deploy to preview
vercel --prod            # Deploy to production
vercel logs              # View function logs
vercel env ls            # List environment variables

# Local testing
python api/health.py     # Test health endpoint
python test_structure.py # Test system components
python -m pytest tests/ # Run test suite

# Monitoring
vercel logs --follow     # Follow logs in real-time
vercel inspect <url>     # Inspect specific deployment
```

## Conclusion

Your Youth Program Insights RAG system is now deployed and ready to provide AI-powered insights from youth program survey data. The system is designed to be scalable, reliable, and cost-effective while providing excellent user experience through intelligent error handling and user-friendly responses.

Remember to monitor the system regularly and keep dependencies updated for optimal performance and security.