# API Documentation

## Overview

The Advanced RAG System provides a RESTful API for querying youth program survey data using AI-powered semantic search and conversational interfaces. The API is deployed on Vercel and includes comprehensive error handling with user-friendly responses.

**Base URL**: `https://your-deployment-url.vercel.app`

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing API key authentication or other security measures.

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- **Default Limit**: 100 requests per hour per IP
- **Rate Limit Headers**: Included in responses
- **Exceeded Limit**: Returns 429 status with retry information

## Error Handling

The API provides user-friendly error responses with actionable guidance:

### Error Response Format
```json
{
  "success": false,
  "error": {
    "type": "validation|timeout|external_service|rate_limit|authentication|unknown",
    "title": "Human-readable error title",
    "message": "Clear explanation of what went wrong",
    "suggestions": [
      "Actionable step 1",
      "Actionable step 2",
      "Actionable step 3"
    ],
    "retry": {
      "recommended": true,
      "wait_seconds": 30,
      "message": "Try again in 30 seconds"
    },
    "support": {
      "message": "If this problem continues, please contact our support team",
      "email": "support@example.com"
    },
    "timestamp": "2025-08-25T15:30:45.123Z"
  },
  "service": {
    "name": "Youth Program Insights",
    "status": "degraded"
  }
}
```

## Endpoints

### 1. Search API

Perform semantic search queries against youth program survey data.

#### `POST /api/search`

**Description**: Search for relevant survey responses using natural language queries.

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "query": "How do programs build confidence in young people?",
  "max_results": 5,
  "filters": {
    "age_group": ["13-15", "16-18"],
    "organization": ["YCUK", "Palace for Life"],
    "gender": ["Male", "Female"]
  }
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Natural language search query (max 1000 characters) |
| `max_results` | integer | No | Number of results to return (1-20, default: 5) |
| `filters` | object | No | Filter results by metadata |
| `filters.age_group` | array | No | Filter by age groups: ["13-15", "16-18", "19-25"] |
| `filters.organization` | array | No | Filter by organization names |
| `filters.gender` | array | No | Filter by gender: ["Male", "Female"] |

**Success Response** (200 OK):
```json
{
  "success": true,
  "query": "How do programs build confidence in young people?",
  "answer": "Based on survey responses from youth programs, confidence is built through several key mechanisms. Young people report that structured activities and skill-building workshops help them develop new abilities, which directly contributes to self-confidence. Peer support and mentorship relationships also play a crucial role...",
  "evidence_count": 5,
  "source_documents": [
    {
      "text": "The program really helped me believe in myself. Through the workshops and support from mentors, I learned that I could achieve things I never thought possible.",
      "organization": "YCUK",
      "age_group": "16-18",
      "gender": "Female",
      "question_text": "How has this program impacted your confidence?",
      "similarity_score": 0.89
    }
  ],
  "metadata": {
    "organizations": ["YCUK", "Palace for Life"],
    "age_groups": ["13-15", "16-18"],
    "genders": ["Male", "Female"],
    "system_type": "serverless_rag",
    "processing_time": 2.1
  },
  "filters_applied": {
    "age_group": ["13-15", "16-18"]
  },
  "timestamp": "2025-08-25T15:30:45.123Z"
}
```

**Example Requests**:

1. **Basic Search**:
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the benefits of youth programs?"
  }'
```

2. **Filtered Search**:
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do programs help with social skills?",
    "max_results": 3,
    "filters": {
      "age_group": ["16-18"],
      "organization": ["YCUK"]
    }
  }'
```

3. **Gender-Specific Analysis**:
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What differences exist between male and female experiences?",
    "max_results": 10,
    "filters": {
      "gender": ["Male", "Female"]
    }
  }'
```

### 2. Chat API

Engage in conversational interactions with context awareness and session management.

#### `POST /api/chat`

**Description**: Have a conversation about youth program data with context awareness and follow-up capabilities.

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "What are the main benefits of youth programs?",
  "session_id": "user_123",
  "include_context": true,
  "max_results": 5
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | Conversational message (max 1000 characters) |
| `session_id` | string | No | Session identifier for conversation continuity (default: "default") |
| `include_context` | boolean | No | Whether to use conversation context (default: true) |
| `max_results` | integer | No | Number of source documents to consider (1-20, default: 5) |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Youth programs offer several key benefits based on participant feedback. The most commonly mentioned benefits include building confidence and self-esteem, developing social connections and friendships, learning new skills and abilities, and having access to mentorship and guidance...",
  "evidence_count": 5,
  "source_documents": [
    {
      "text": "This program changed my life. I made friends, learned new skills, and most importantly, I believe in myself now.",
      "organization": "Palace for Life",
      "age_group": "16-18",
      "gender": "Male",
      "question_text": "What has been the most important outcome for you?",
      "similarity_score": 0.92
    }
  ],
  "metadata": {
    "organizations": ["YCUK", "Palace for Life"],
    "age_groups": ["13-15", "16-18", "19-25"],
    "genders": ["Male", "Female"],
    "session_id": "user_123",
    "turn_number": 1,
    "conversation_context_used": false,
    "processing_time": 1.8,
    "system_type": "conversational_rag"
  },
  "conversation": {
    "session_id": "user_123",
    "turn_number": 1,
    "context_used": false,
    "is_follow_up": false
  },
  "timestamp": "2025-08-25T15:30:45.123Z"
}
```

**Example Conversation Flow**:

1. **Initial Question**:
```bash
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main benefits of youth programs?",
    "session_id": "conversation_1"
  }'
```

2. **Follow-up Question**:
```bash
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you tell me more about the confidence building aspect?",
    "session_id": "conversation_1"
  }'
```

3. **Specific Follow-up**:
```bash
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How does this differ between age groups?",
    "session_id": "conversation_1"
  }'
```

### 3. Health Check API

Monitor system health and component status.

#### `GET /api/health`

**Description**: Check the health status of the system and its components.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `detailed` | boolean | No | Return detailed component health information |

**Basic Health Check**:
```bash
curl https://your-deployment-url.vercel.app/api/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-08-25T15:30:45.123Z",
  "service": "Youth Program Insights",
  "version": "1.0.0",
  "environment": "production",
  "region": "us-east-1",
  "response_time": 0.234
}
```

**Detailed Health Check**:
```bash
curl https://your-deployment-url.vercel.app/api/health?detailed=true
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-08-25T15:30:45.123Z",
  "service": "Youth Program Insights",
  "version": "1.0.0",
  "environment": "production",
  "region": "us-east-1",
  "components": {
    "rag_engine": {
      "status": "healthy",
      "components": {
        "vector_store": "healthy",
        "llm": "healthy",
        "embeddings": "healthy"
      },
      "config": {
        "vector_store_type": "pinecone",
        "llm_model": "gemini-1.5-flash",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
      },
      "check_time": 0.156
    },
    "vector_store": {
      "status": "healthy",
      "stats": {
        "total_vectors": 1000,
        "dimension": 384,
        "index_fullness": 0.02,
        "vector_store_type": "pinecone",
        "index_name": "rag-survey-responses"
      }
    }
  },
  "environment": {
    "variables": {
      "GOOGLE_API_KEY": true,
      "PINECONE_API_KEY": true,
      "PINECONE_ENVIRONMENT": true,
      "PINECONE_INDEX_NAME": true
    },
    "missing": []
  },
  "performance": {
    "cold_start": false,
    "memory_usage": {
      "rss_mb": 245.6,
      "percent": 24.0
    },
    "startup_time": 1234567890.123
  },
  "system": {
    "python_version": "3.9.18",
    "platform": "linux",
    "vercel_env": "production",
    "vercel_region": "iad1",
    "function_name": "api/health.py",
    "deployment_id": "dpl_abc123"
  },
  "response_time": 0.456
}
```

**Health Status Values**:
- `healthy`: All components functioning normally
- `degraded`: Some components have issues but system is functional
- `unhealthy`: Critical components are failing

### 4. Statistics API

Get system statistics and performance metrics.

#### `GET /api/stats`

**Description**: Retrieve system statistics, usage metrics, and performance data.

**Request**:
```bash
curl https://your-deployment-url.vercel.app/api/stats
```

**Response** (200 OK):
```json
{
  "system_type": "serverless_rag",
  "vector_store": {
    "total_vectors": 1000,
    "dimension": 384,
    "index_fullness": 0.02,
    "namespaces": {
      "production": {
        "vector_count": 950
      },
      "staging": {
        "vector_count": 50
      }
    },
    "vector_store_type": "pinecone",
    "index_name": "rag-survey-responses",
    "environment": "gcp-starter"
  },
  "config": {
    "llm_model": "gemini-1.5-flash",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "max_results": 5,
    "temperature": 0.1,
    "max_tokens": 1000,
    "timeout_seconds": 25
  },
  "performance": {
    "average_response_time": 2.1,
    "cache_hit_rate": 0.15,
    "error_rate": 0.02
  },
  "usage": {
    "total_queries": 1500,
    "queries_today": 45,
    "most_common_topics": [
      "confidence building",
      "social skills",
      "program benefits"
    ]
  },
  "timestamp": "2025-08-25T15:30:45.123Z"
}
```

## Usage Examples

### Common Query Patterns

#### 1. General Program Benefits
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main benefits young people get from these programs?"
  }'
```

#### 2. Confidence and Self-Esteem
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do programs help build confidence and self-esteem?"
  }'
```

#### 3. Social Skills and Relationships
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What do participants say about making friends and social connections?"
  }'
```

#### 4. Age Group Comparisons
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do program experiences differ between younger and older participants?",
    "max_results": 10,
    "filters": {
      "age_group": ["13-15", "16-18", "19-25"]
    }
  }'
```

#### 5. Gender Analysis
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Are there differences in how male and female participants experience programs?",
    "filters": {
      "gender": ["Male", "Female"]
    }
  }'
```

#### 6. Organization-Specific Insights
```bash
curl -X POST https://your-deployment-url.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What unique approaches does this organization take?",
    "filters": {
      "organization": ["YCUK"]
    }
  }'
```

### Conversational Examples

#### Research Conversation Flow
```bash
# Start with broad question
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am researching youth program effectiveness. What are the key outcomes?",
    "session_id": "research_session"
  }'

# Follow up with specific aspect
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you elaborate on the confidence building outcomes?",
    "session_id": "research_session"
  }'

# Ask for specific examples
curl -X POST https://your-deployment-url.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Do you have specific quotes from participants about confidence?",
    "session_id": "research_session"
  }'
```

## Integration Guide

### JavaScript/Node.js Integration

```javascript
class YouthProgramAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async search(query, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        max_results: options.maxResults || 5,
        filters: options.filters || {}
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Search failed');
    }

    return await response.json();
  }

  async chat(message, sessionId = 'default', includeContext = true) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        include_context: includeContext
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Chat failed');
    }

    return await response.json();
  }

  async healthCheck(detailed = false) {
    const url = `${this.baseUrl}/api/health${detailed ? '?detailed=true' : ''}`;
    const response = await fetch(url);
    return await response.json();
  }
}

// Usage example
const api = new YouthProgramAPI('https://your-deployment-url.vercel.app');

// Search example
try {
  const result = await api.search('How do programs build confidence?', {
    maxResults: 3,
    filters: { age_group: ['16-18'] }
  });
  console.log('Answer:', result.answer);
  console.log('Evidence count:', result.evidence_count);
} catch (error) {
  console.error('Search error:', error.message);
}

// Chat example
try {
  const response = await api.chat('What are the main benefits?', 'user_123');
  console.log('Response:', response.message);
} catch (error) {
  console.error('Chat error:', error.message);
}
```

### Python Integration

```python
import requests
import json

class YouthProgramAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search(self, query, max_results=5, filters=None):
        """Search for relevant survey responses"""
        url = f"{self.base_url}/api/search"
        payload = {
            "query": query,
            "max_results": max_results,
            "filters": filters or {}
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def chat(self, message, session_id="default", include_context=True):
        """Have a conversation about the data"""
        url = f"{self.base_url}/api/chat"
        payload = {
            "message": message,
            "session_id": session_id,
            "include_context": include_context
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def health_check(self, detailed=False):
        """Check system health"""
        url = f"{self.base_url}/api/health"
        if detailed:
            url += "?detailed=true"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self):
        """Get system statistics"""
        url = f"{self.base_url}/api/stats"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

# Usage example
api = YouthProgramAPI('https://your-deployment-url.vercel.app')

try:
    # Search example
    result = api.search(
        query='How do programs build confidence?',
        max_results=3,
        filters={'age_group': ['16-18']}
    )
    print(f"Answer: {result['answer']}")
    print(f"Evidence count: {result['evidence_count']}")
    
    # Chat example
    response = api.chat('What are the main benefits?', session_id='user_123')
    print(f"Response: {response['message']}")
    
    # Health check
    health = api.health_check(detailed=True)
    print(f"System status: {health['status']}")
    
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")
```

### cURL Examples for Testing

```bash
#!/bin/bash

# Set your API base URL
BASE_URL="https://your-deployment-url.vercel.app"

# Test health check
echo "Testing health check..."
curl -s "$BASE_URL/api/health" | jq '.'

# Test basic search
echo "Testing basic search..."
curl -s -X POST "$BASE_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do programs help young people?"
  }' | jq '.answer'

# Test filtered search
echo "Testing filtered search..."
curl -s -X POST "$BASE_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about confidence building?",
    "max_results": 3,
    "filters": {
      "age_group": ["16-18"]
    }
  }' | jq '.evidence_count'

# Test chat
echo "Testing chat..."
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about the benefits",
    "session_id": "test_session"
  }' | jq '.message'

# Test error handling
echo "Testing error handling..."
curl -s -X POST "$BASE_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.error'

echo "All tests completed!"
```

## Best Practices

### Query Optimization

1. **Be Specific**: More specific queries yield better results
   ```json
   // Good
   {"query": "How do programs help with social anxiety in teenagers?"}
   
   // Less effective
   {"query": "programs help"}
   ```

2. **Use Filters**: Narrow down results with appropriate filters
   ```json
   {
     "query": "confidence building strategies",
     "filters": {
       "age_group": ["16-18"],
       "organization": ["YCUK"]
     }
   }
   ```

3. **Appropriate Result Limits**: Balance comprehensiveness with performance
   ```json
   // For quick insights
   {"max_results": 3}
   
   // For comprehensive analysis
   {"max_results": 10}
   ```

### Error Handling

1. **Always Handle Errors**: Check response status and handle errors gracefully
2. **Use Error Messages**: Display user-friendly error messages from the API
3. **Implement Retry Logic**: For timeout and service unavailable errors
4. **Respect Rate Limits**: Implement appropriate delays between requests

### Performance Optimization

1. **Cache Results**: Cache frequently requested data on the client side
2. **Use Appropriate Timeouts**: Set reasonable timeouts for your requests
3. **Monitor Performance**: Track response times and optimize accordingly
4. **Batch Requests**: When possible, combine multiple queries efficiently

### Security Considerations

1. **Validate Input**: Always validate user input before sending to API
2. **Use HTTPS**: Always use HTTPS for API requests
3. **Handle Sensitive Data**: Be careful with any sensitive information in queries
4. **Monitor Usage**: Track API usage to detect unusual patterns

This API documentation provides comprehensive information for integrating with the Advanced RAG System. For additional support or questions, refer to the troubleshooting guide or contact the support team.