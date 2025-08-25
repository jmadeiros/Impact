# User-Friendly Error Response System

## Overview

The user-friendly error response system transforms technical errors into clear, helpful messages that end users can understand and act upon. This system is designed to improve user experience by providing meaningful guidance when things go wrong.

## Key Principles

### 1. Clear Communication
- Use plain language instead of technical jargon
- Explain what happened in terms users understand
- Avoid error codes and technical details in user-facing messages

### 2. Actionable Guidance
- Provide specific steps users can take to resolve issues
- Prioritize the most likely solutions first
- Include timeframes for retries when appropriate

### 3. Empathetic Tone
- Acknowledge the user's frustration
- Take responsibility without blaming the user
- Reassure users that issues are typically temporary

### 4. Context Awareness
- Adapt messages based on the user's query and situation
- Consider factors like query complexity and retry attempts
- Provide relevant suggestions based on error type

## Error Types and Messages

### Timeout Errors
**What users see:**
- **Title:** "Taking longer than expected"
- **Message:** "I'm taking a bit longer to process your request than usual. This might be due to high demand or a complex query."
- **Suggestions:**
  - Try asking a simpler or more specific question
  - Break complex questions into smaller parts
  - Wait a moment and try again - the service may be busy

### Memory Limit Errors
**What users see:**
- **Title:** "Request too complex"
- **Message:** "Your request requires more processing power than I currently have available. Try simplifying your question or breaking it into smaller parts."
- **Suggestions:**
  - Ask for fewer results in your query
  - Try a more specific question that requires less data processing
  - Break your question into smaller, focused parts

### External Service Errors
**What users see:**
- **Title:** "Service temporarily unavailable"
- **Message:** "I'm having trouble connecting to my knowledge base right now. This is usually temporary and should resolve shortly."
- **Suggestions:**
  - Wait a few minutes and try your question again
  - Check your internet connection
  - Try a different question to see if the service is working

### Rate Limit Errors
**What users see:**
- **Title:** "Too many requests"
- **Message:** "You're asking questions faster than I can process them. Please wait a moment before trying again."
- **Suggestions:**
  - Wait 30-60 seconds before asking another question
  - Slow down the pace of your requests
  - Consider combining multiple questions into one

### Validation Errors
**What users see:**
- **Title:** "Problem with [field name]"
- **Message:** "There's an issue with [field]: [specific issue]"
- **Example:** Correct format shown
- **Suggestions:**
  - Check that [field] is properly formatted
  - Make sure [field] meets the requirements
  - Try the example format shown

## Response Structure

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "type": "timeout",
    "title": "Taking longer than expected",
    "message": "I'm taking a bit longer to process your request than usual...",
    "suggestions": [
      "Try asking a simpler or more specific question",
      "Break complex questions into smaller parts",
      "Wait a moment and try again - the service may be busy"
    ],
    "timestamp": "2025-08-25T15:30:45.123Z",
    "retry": {
      "recommended": true,
      "wait_seconds": 30,
      "message": "Try again in 30 seconds"
    },
    "support": {
      "message": "If this problem continues, please contact our support team",
      "email": "support@example.com",
      "include_error_id": true
    }
  },
  "query": "How do programs build confidence?",
  "service": {
    "name": "Youth Program Insights",
    "status": "degraded"
  }
}
```

### Fallback Response
```json
{
  "success": false,
  "query": "How do programs build confidence?",
  "answer": "I'm taking longer than usual to process questions right now. While I work on getting back to full speed, you might try asking a simpler version of your question.",
  "evidence_count": 0,
  "source_documents": [],
  "metadata": {
    "system_type": "user_friendly_fallback",
    "error_type": "timeout",
    "fallback": true,
    "user_friendly": true
  },
  "error_info": {
    "title": "Taking longer than expected",
    "suggestions": [
      "Try asking a simpler or more specific question",
      "Break complex questions into smaller parts"
    ],
    "retry_in_seconds": 30
  },
  "timestamp": "2025-08-25T15:30:45.123Z"
}
```

### Validation Error Response
```json
{
  "success": false,
  "error": {
    "type": "validation",
    "title": "Problem with your question",
    "message": "There's an issue with your question: cannot be empty",
    "field": "query",
    "suggestions": [
      "Check that your question is properly formatted",
      "Make sure your question meets the requirements",
      "Try the example format shown below"
    ],
    "example": {
      "message": "Here's an example of the correct format:",
      "data": {
        "query": "How do programs build confidence?",
        "max_results": 5
      }
    },
    "timestamp": "2025-08-25T15:30:45.123Z"
  }
}
```

## Implementation

### Basic Usage

```python
from user_friendly_errors import (
    format_user_friendly_error, 
    create_user_friendly_fallback,
    format_validation_error
)

# Format a technical error for users
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    user_response = format_user_friendly_error(
        error=e,
        user_query="How do programs help?",
        context={"query_length": 50, "retry_count": 0}
    )
    return user_response

# Create a fallback response
fallback = create_user_friendly_fallback(
    user_query="What are the benefits?",
    error_type=ErrorType.TIMEOUT
)

# Format validation errors
validation_error = format_validation_error(
    field_name="query",
    issue="cannot be empty",
    example={"query": "How do programs help?"}
)
```

### API Integration

```python
@timeout_handler(25)
@memory_monitor
def api_handler(request):
    try:
        # Process request
        result = process_request(request)
        return success_response(result)
        
    except ServerlessError as e:
        # Get user query for context
        user_query = request.get('query', 'your question')
        
        # Create context for better error messages
        context = {
            'query_length': len(user_query),
            'retry_count': get_retry_count(request),
            'peak_hours': is_peak_hours()
        }
        
        # Format user-friendly error
        error_response = format_user_friendly_error(e, context, user_query)
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_response)
        }
```

### Configuration

```python
# Production configuration (minimal technical details)
config = {
    "include_technical_details": False,
    "include_contact_info": True,
    "support_email": "support@yourservice.com",
    "service_name": "Your Service Name",
    "max_suggestion_count": 3,
    "include_retry_info": True
}

formatter = UserFriendlyErrorFormatter(config)
```

## Context-Aware Messages

The system adapts messages based on context:

### Long Queries
- **Timeout:** "Your question is quite long, which might be contributing to the delay."
- **Memory:** "Your question is quite detailed, which requires more processing power."

### Multiple Retries
- **Any Error:** "I notice you've tried this 3 time(s) already."

### Peak Hours
- **Timeout/Rate Limit:** "We're experiencing higher than usual demand right now."

## Best Practices

### 1. Message Writing
- Start with what happened in simple terms
- Explain why it might have occurred
- Provide clear next steps
- End with reassurance when appropriate

### 2. Suggestion Ordering
- Most likely solution first
- Quick fixes before complex ones
- Self-service before contacting support
- Immediate actions before delayed ones

### 3. Tone Guidelines
- Be conversational but professional
- Show empathy without over-apologizing
- Be confident in your suggestions
- Avoid technical blame or excuses

### 4. Context Usage
- Consider the user's journey and frustration level
- Adapt suggestions based on what they've already tried
- Account for system load and external factors
- Personalize when possible without being intrusive

## Testing

### Message Quality Assessment
Each error message is evaluated on:
- **Clarity:** Uses plain language (2 points)
- **Empathy:** Shows understanding (2 points)
- **Explanation:** Adequate detail (2 points)
- **Actionability:** Useful suggestions (2 points)
- **Reassurance:** Indicates temporary nature (2 points)

### Test Coverage
- Error message quality and tone
- Context-aware message adaptation
- Validation error formatting
- Fallback response generation
- API integration compatibility
- Configuration option handling
- Response structure completeness

### Running Tests
```bash
python3 vercel-deployment/test_user_friendly_errors.py
```

## Monitoring and Improvement

### Metrics to Track
- Error message clarity ratings
- User retry rates after errors
- Support ticket volume for different error types
- User satisfaction with error explanations

### Continuous Improvement
- Regularly review error message effectiveness
- Update suggestions based on user feedback
- Refine context-aware adaptations
- Add new error scenarios as they emerge

## Integration with Support

### Error IDs
Each error generates a unique ID for support tracking:
```
TIMEOUT_a1b2c3d4
MEMORY_LIMIT_e5f6g7h8
```

### Support Information
Errors include contact information when configured:
```json
{
  "support": {
    "message": "If this problem continues, please contact our support team",
    "email": "support@example.com",
    "include_error_id": true
  }
}
```

### Escalation Guidelines
- **Validation Errors:** User can fix themselves
- **Timeout/Memory:** Retry recommended
- **External Service:** Wait and retry
- **Authentication:** Contact support immediately
- **Unknown:** Try again, then contact support

This user-friendly error system ensures that when things go wrong, users receive helpful, actionable guidance that improves their experience and reduces frustration.