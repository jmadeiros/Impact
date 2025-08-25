# Troubleshooting Guide

## Common Deployment Issues

### Environment Variable Problems

#### Issue: "Missing required configuration" errors
**Symptoms:**
```
❌ Pinecone Error: Missing required Pinecone configuration: ['pinecone_api_key', 'pinecone_environment']
```

**Solutions:**
1. **Verify environment variables in Vercel dashboard:**
   - Go to Project Settings → Environment Variables
   - Check all required variables are present
   - Ensure variables are enabled for correct environment (Production/Preview)

2. **Check variable names (case-sensitive):**
   ```bash
   # Correct names:
   PINECONE_API_KEY (not pinecone_api_key)
   GOOGLE_API_KEY (not google_api_key)
   ```

3. **Test locally first:**
   ```bash
   python3 test_env_loading.py
   ```

#### Issue: Environment variables not loading in functions
**Symptoms:** Variables work locally but not in deployed functions

**Solutions:**
1. **Check environment scope:**
   - Ensure variables are set for Production environment
   - Redeploy after adding variables: `vercel --prod`

2. **Verify vercel.json configuration:**
   ```json
   {
     "build": {
       "env": {
         "PYTHONPATH": "./lib"
       }
     }
   }
   ```

### API Connection Issues

#### Issue: Pinecone connection failures
**Symptoms:**
```
ERROR: (401) Unauthorized
HTTP response body: Invalid API Key
```

**Solutions:**
1. **Verify API key validity:**
   ```bash
   # Test API key locally
   python3 -c "
   from pinecone import Pinecone
   pc = Pinecone(api_key='your-api-key')
   print(pc.list_indexes())
   "
   ```

2. **Check Pinecone environment:**
   - Ensure `PINECONE_ENVIRONMENT` matches your index environment
   - Common environments: `gcp-starter`, `us-west1-gcp`, `us-east1-gcp`

3. **Verify index exists:**
   - Check Pinecone console for index name
   - Ensure index has correct dimensions (384 for all-MiniLM-L6-v2)

#### Issue: Google AI API failures
**Symptoms:**
```
google.api_core.exceptions.PermissionDenied: 403 API key not valid
```

**Solutions:**
1. **Verify API key permissions:**
   - Go to Google Cloud Console → Credentials
   - Check API key restrictions
   - Ensure Generative Language API is enabled

2. **Test API key:**
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_API_KEY"
   ```

### Function Timeout Issues

#### Issue: Functions timing out
**Symptoms:**
```
Error: Function execution timeout
Task timed out after 25.00 seconds
```

**Solutions:**
1. **Optimize query complexity:**
   ```bash
   # Reduce max_results
   curl -X POST https://your-url.vercel.app/api/search \
     -d '{"query": "simple query", "max_results": 3}'
   ```

2. **Check vector store performance:**
   ```bash
   # Test vector store response time
   python3 -c "
   import time
   from lib.vector_client import VectorStoreFactory
   client = VectorStoreFactory.create_from_env()
   start = time.time()
   client.health_check()
   print(f'Health check: {time.time() - start:.2f}s')
   "
   ```

3. **Increase timeout (max 25s for hobby plan):**
   ```json
   // vercel.json
   {
     "functions": {
       "api/*.py": {
         "maxDuration": 25
       }
     }
   }
   ```

#### Issue: Cold start performance
**Symptoms:** First request takes > 10 seconds

**Solutions:**
1. **This is normal for serverless functions**
2. **Optimize imports:**
   ```python
   # Use lazy imports in functions
   def handler(request):
       from lib.rag_engine import ServerlessRAGEngine
       # ... rest of function
   ```

3. **Consider Vercel Pro plan for better cold start performance**

### Memory Issues

#### Issue: Out of memory errors
**Symptoms:**
```
Error: Function exceeded memory limit
MemoryError: Unable to allocate array
```

**Solutions:**
1. **Reduce batch sizes:**
   ```python
   # In vector operations
   batch_size = 50  # Reduce from 100
   ```

2. **Optimize data structures:**
   ```python
   # Use generators instead of lists for large datasets
   def process_documents():
       for doc in documents:
           yield process(doc)
   ```

3. **Increase memory limit:**
   ```json
   // vercel.json
   {
     "functions": {
       "api/*.py": {
         "memory": 1024
       }
     }
   }
   ```

### Data Migration Issues

#### Issue: ChromaDB export fails
**Symptoms:**
```
Error: No such collection: survey_responses
```

**Solutions:**
1. **Check collection name:**
   ```python
   # In export script
   collection_name = "your_actual_collection_name"
   ```

2. **Verify ChromaDB path:**
   ```python
   # Check ChromaDB directory
   import os
   print(os.listdir("./chromadb"))
   ```

#### Issue: Pinecone migration fails
**Symptoms:**
```
Error: Dimension mismatch: expected 384, got 768
```

**Solutions:**
1. **Check embedding model dimensions:**
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   print(f"Dimensions: {model.get_sentence_embedding_dimension()}")
   ```

2. **Recreate Pinecone index with correct dimensions:**
   - Delete existing index
   - Create new index with 384 dimensions

### API Response Issues

#### Issue: User-friendly errors not showing
**Symptoms:** Users see technical error messages

**Solutions:**
1. **Check error handling imports:**
   ```python
   from user_friendly_errors import format_user_friendly_error
   ```

2. **Verify error handling configuration:**
   ```bash
   # Set in environment variables
   INCLUDE_TECHNICAL_DETAILS=false
   INCLUDE_CONTACT_INFO=true
   ```

#### Issue: Search returns no results
**Symptoms:** Valid queries return empty results

**Solutions:**
1. **Check vector store data:**
   ```bash
   curl https://your-url.vercel.app/api/stats
   # Should show total_vectors > 0
   ```

2. **Test embedding generation:**
   ```python
   from lib.embeddings import EmbeddingClient
   client = EmbeddingClient()
   embedding = client.generate_embedding("test query")
   print(f"Embedding length: {len(embedding)}")
   ```

3. **Verify query processing:**
   ```bash
   # Test with simple query
   curl -X POST https://your-url.vercel.app/api/search \
     -d '{"query": "test", "max_results": 1}'
   ```

## Performance Issues

### Slow Response Times

#### Issue: API responses taking > 5 seconds
**Symptoms:** Slow user experience, potential timeouts

**Solutions:**
1. **Profile function performance:**
   ```bash
   # Check function logs for timing
   vercel logs --follow
   ```

2. **Optimize vector search:**
   ```python
   # Reduce search scope
   max_results = 3  # Instead of 10
   ```

3. **Implement caching:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def cached_search(query_hash):
       # Expensive operations
       pass
   ```

### High Memory Usage

#### Issue: Functions approaching memory limits
**Symptoms:** Memory warnings in logs

**Solutions:**
1. **Monitor memory usage:**
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

2. **Optimize data loading:**
   ```python
   # Load data in chunks
   def process_in_chunks(data, chunk_size=100):
       for i in range(0, len(data), chunk_size):
           yield data[i:i + chunk_size]
   ```

## Debugging Tools

### Enable Debug Mode

```bash
# Set debug environment variables
vercel env add DEBUG true
vercel env add INCLUDE_STACK_TRACES true
vercel env add INCLUDE_TECHNICAL_DETAILS true

# Redeploy
vercel --prod
```

### Local Debugging

```bash
# Run local development server
vercel dev

# Test with debug output
python3 -c "
import os
os.environ['DEBUG'] = 'true'
from api.search import handler
# Test handler locally
"
```

### Log Analysis

```bash
# View function logs
vercel logs --follow

# Filter for errors
vercel logs | grep ERROR

# View specific function logs
vercel logs api/search.py
```

### Health Check Debugging

```bash
# Detailed health check
curl https://your-url.vercel.app/api/health?detailed=true

# Check individual components
python3 test_env_loading.py
python3 test_structure.py
```

## Getting Help

### Check System Status
1. **Vercel Status**: [status.vercel.com](https://status.vercel.com)
2. **Pinecone Status**: [status.pinecone.io](https://status.pinecone.io)
3. **Google Cloud Status**: [status.cloud.google.com](https://status.cloud.google.com)

### Collect Debug Information

Before contacting support, collect:

```bash
# System information
curl https://your-url.vercel.app/api/health?detailed=true > health_check.json

# Recent logs
vercel logs > recent_logs.txt

# Environment check
python3 test_env_loading.py > env_check.txt

# Configuration
vercel env ls > env_vars.txt
```

### Support Channels
- **Vercel Support**: [vercel.com/support](https://vercel.com/support)
- **Pinecone Support**: [pinecone.io/support](https://pinecone.io/support)
- **Google Cloud Support**: [cloud.google.com/support](https://cloud.google.com/support)

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| 401 | Unauthorized API access | Check API keys |
| 403 | Forbidden/Permission denied | Verify API permissions |
| 404 | Resource not found | Check URLs and endpoints |
| 429 | Rate limit exceeded | Implement retry logic |
| 500 | Internal server error | Check function logs |
| 503 | Service unavailable | Check external service status |
| 504 | Gateway timeout | Optimize function performance |

This troubleshooting guide covers the most common issues you might encounter. For specific problems not covered here, enable debug mode and check the detailed logs for more information.