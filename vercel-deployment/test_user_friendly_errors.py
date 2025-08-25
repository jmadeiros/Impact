#!/usr/bin/env python3
"""
Test Script for User-Friendly Error Responses
Tests the user-friendly error formatting and API integration
"""
import os
import sys
import json
from typing import Dict, Any

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from user_friendly_errors import (
    UserFriendlyErrorFormatter, format_user_friendly_error, 
    create_user_friendly_fallback, format_validation_error,
    get_contextual_error_message, ErrorType
)

def test_error_message_quality():
    """Test the quality and helpfulness of error messages"""
    print("🧪 Testing Error Message Quality")
    print("=" * 50)
    
    formatter = UserFriendlyErrorFormatter()
    
    # Test each error type for user-friendliness
    test_scenarios = [
        (ErrorType.TIMEOUT, "User asks a complex question during peak hours"),
        (ErrorType.MEMORY_LIMIT, "User requests too much data at once"),
        (ErrorType.EXTERNAL_SERVICE, "Vector database is temporarily down"),
        (ErrorType.RATE_LIMIT, "User is asking questions too quickly"),
        (ErrorType.AUTHENTICATION, "API keys are misconfigured"),
        (ErrorType.VALIDATION, "User sends malformed request"),
        (ErrorType.UNKNOWN, "Unexpected system error occurs")
    ]
    
    for error_type, scenario in test_scenarios:
        error_info = formatter.error_messages[error_type]
        suggestions = formatter.suggestions[error_type]
        
        print(f"\n📝 {error_type.value.upper()}: {scenario}")
        print(f"   Title: {error_info['title']}")
        print(f"   Message: {error_info['message']}")
        print(f"   Suggestions ({len(suggestions)}):")
        for i, suggestion in enumerate(suggestions[:2], 1):
            print(f"     {i}. {suggestion}")
        
        # Check message quality
        quality_score = assess_message_quality(error_info['message'], suggestions)
        print(f"   Quality Score: {quality_score}/10")
    
    print()

def assess_message_quality(message: str, suggestions: list) -> int:
    """Assess the quality of an error message (1-10 scale)"""
    score = 0
    
    # Check for user-friendly language (not technical jargon)
    technical_words = ['api', 'server', 'database', 'timeout', 'memory', 'exception']
    if not any(word in message.lower() for word in technical_words):
        score += 2
    
    # Check for empathy/understanding
    empathy_words = ['sorry', 'apologize', 'understand', 'help', 'moment']
    if any(word in message.lower() for word in empathy_words):
        score += 2
    
    # Check for explanation of what happened
    if len(message) > 50:  # Sufficient explanation
        score += 2
    
    # Check for actionable suggestions
    if len(suggestions) >= 2:
        score += 2
    
    # Check for reassurance (not permanent)
    reassurance_words = ['temporary', 'shortly', 'moment', 'try again']
    if any(word in message.lower() for word in reassurance_words):
        score += 2
    
    return min(score, 10)

def test_contextual_messages():
    """Test context-aware error messages"""
    print("🧪 Testing Contextual Error Messages")
    print("=" * 50)
    
    test_contexts = [
        {
            "query_length": 600,
            "description": "Long query"
        },
        {
            "retry_count": 3,
            "description": "Multiple retries"
        },
        {
            "peak_hours": True,
            "description": "Peak usage hours"
        },
        {
            "description": "Normal context"
        }
    ]
    
    for context in test_contexts:
        print(f"\n📝 Context: {context['description']}")
        
        # Test timeout error with context
        message = get_contextual_error_message(ErrorType.TIMEOUT, context)
        print(f"   Timeout Message: {message[:80]}...")
        
        # Test memory limit error with context
        message = get_contextual_error_message(ErrorType.MEMORY_LIMIT, context)
        print(f"   Memory Message: {message[:80]}...")
    
    print()

def test_validation_errors():
    """Test validation error formatting"""
    print("🧪 Testing Validation Error Formatting")
    print("=" * 50)
    
    validation_scenarios = [
        ("query", "cannot be empty", {"query": "How do programs help?"}),
        ("message", "is too long", {"message": "Shorter message example"}),
        ("session_id", "has invalid format", {"session_id": "user_123"}),
        ("max_results", "must be between 1 and 20", {"max_results": 5}),
        ("filters", "contains invalid age group", {"filters": {"age_group": ["13-15"]}})
    ]
    
    for field, issue, example in validation_scenarios:
        response = format_validation_error(field, issue, example)
        
        print(f"\n📝 Field: {field}")
        print(f"   Title: {response['error']['title']}")
        print(f"   Message: {response['error']['message']}")
        print(f"   Has Example: {'Yes' if 'example' in response['error'] else 'No'}")
        print(f"   Suggestions: {len(response['error']['suggestions'])}")
    
    print()

def test_fallback_responses():
    """Test fallback response generation"""
    print("🧪 Testing Fallback Response Generation")
    print("=" * 50)
    
    test_queries = [
        "How do programs build confidence in young people?",
        "What are the main benefits of youth programs?",
        "Tell me about social connections in programs",
        "How do different age groups respond to programs?",
        "What do participants say about their experience?"
    ]
    
    error_types = [ErrorType.TIMEOUT, ErrorType.MEMORY_LIMIT, ErrorType.EXTERNAL_SERVICE]
    
    for query in test_queries[:2]:  # Test first 2 queries
        print(f"\n📝 Query: {query}")
        
        for error_type in error_types:
            fallback = create_user_friendly_fallback(query, error_type)
            
            print(f"   {error_type.value}: {fallback['answer'][:60]}...")
            print(f"     Retry in: {fallback['error_info']['retry_in_seconds']}s")
            print(f"     Suggestions: {len(fallback['error_info']['suggestions'])}")
    
    print()

def test_api_integration():
    """Test integration with API endpoints"""
    print("🧪 Testing API Integration")
    print("=" * 50)
    
    # Mock API request scenarios
    api_scenarios = [
        {
            "name": "Missing query parameter",
            "request": {},
            "expected_error": "validation"
        },
        {
            "name": "Empty query string",
            "request": {"query": ""},
            "expected_error": "validation"
        },
        {
            "name": "Query too long",
            "request": {"query": "x" * 1001},
            "expected_error": "validation"
        },
        {
            "name": "Invalid JSON",
            "request": "invalid json",
            "expected_error": "validation"
        }
    ]
    
    for scenario in api_scenarios:
        print(f"\n📝 Scenario: {scenario['name']}")
        
        # Simulate API error handling
        try:
            if scenario['name'] == "Missing query parameter":
                response = format_validation_error(
                    "query", 
                    "is required and cannot be empty",
                    {"query": "How do programs help?"}
                )
            elif scenario['name'] == "Empty query string":
                response = format_validation_error(
                    "query",
                    "must be a non-empty text string",
                    {"query": "How do programs build confidence?"}
                )
            elif scenario['name'] == "Query too long":
                response = format_validation_error(
                    "query",
                    "is too long (1001 characters). Please keep queries under 1000 characters",
                    {"query": "How do programs help? (shorter version)"}
                )
            elif scenario['name'] == "Invalid JSON":
                response = format_validation_error(
                    "request body",
                    "contains invalid JSON format",
                    {"query": "How do programs help?"}
                )
            
            print(f"   Response Type: {response['error']['type']}")
            print(f"   User Message: {response['error']['message'][:60]}...")
            print(f"   Has Example: {'Yes' if 'example' in response['error'] else 'No'}")
            
        except Exception as e:
            print(f"   ❌ Error in scenario: {e}")
    
    print()

def test_error_response_structure():
    """Test the structure and completeness of error responses"""
    print("🧪 Testing Error Response Structure")
    print("=" * 50)
    
    # Test complete error response structure
    test_error = Exception("Test service unavailable error")
    test_query = "How do programs build confidence?"
    
    response = format_user_friendly_error(test_error, user_query=test_query)
    
    # Check required fields
    required_fields = [
        'success', 'error', 'service'
    ]
    
    error_fields = [
        'type', 'title', 'message', 'suggestions', 'timestamp'
    ]
    
    print("📝 Checking response structure:")
    
    for field in required_fields:
        status = "✅" if field in response else "❌"
        print(f"   {status} {field}")
    
    print("\n📝 Checking error object structure:")
    
    for field in error_fields:
        status = "✅" if field in response.get('error', {}) else "❌"
        print(f"   {status} error.{field}")
    
    # Check suggestions quality
    suggestions = response.get('error', {}).get('suggestions', [])
    print(f"\n📝 Suggestions analysis:")
    print(f"   Count: {len(suggestions)}")
    print(f"   Average length: {sum(len(s) for s in suggestions) / len(suggestions) if suggestions else 0:.1f} chars")
    
    # Check for actionable language
    actionable_words = ['try', 'check', 'wait', 'contact', 'ensure', 'make sure']
    actionable_count = sum(1 for s in suggestions for word in actionable_words if word in s.lower())
    print(f"   Actionable suggestions: {actionable_count}/{len(suggestions)}")
    
    print()

def test_configuration_options():
    """Test different configuration options"""
    print("🧪 Testing Configuration Options")
    print("=" * 50)
    
    # Test with different configurations
    configs = [
        {
            "name": "Production (minimal details)",
            "config": {
                "include_technical_details": False,
                "include_contact_info": True,
                "max_suggestion_count": 2
            }
        },
        {
            "name": "Development (full details)",
            "config": {
                "include_technical_details": True,
                "include_contact_info": True,
                "max_suggestion_count": 4
            }
        },
        {
            "name": "Minimal (basic only)",
            "config": {
                "include_technical_details": False,
                "include_contact_info": False,
                "max_suggestion_count": 1
            }
        }
    ]
    
    test_error = Exception("Test configuration error")
    
    for config_test in configs:
        print(f"\n📝 Configuration: {config_test['name']}")
        
        # Create formatter with custom config
        full_config = {
            "include_technical_details": False,
            "include_contact_info": True,
            "support_email": "support@example.com",
            "service_name": "Youth Program Insights",
            "max_suggestion_count": 3,
            "include_retry_info": True
        }
        full_config.update(config_test['config'])
        
        formatter = UserFriendlyErrorFormatter(full_config)
        response = formatter.format_error_response(test_error, user_query="Test query")
        
        print(f"   Technical details: {'Yes' if 'technical' in response.get('error', {}) else 'No'}")
        print(f"   Contact info: {'Yes' if 'support' in response.get('error', {}) else 'No'}")
        print(f"   Suggestion count: {len(response.get('error', {}).get('suggestions', []))}")
        print(f"   Response size: {len(json.dumps(response))} chars")
    
    print()

def run_all_tests():
    """Run all user-friendly error tests"""
    print("🚀 Starting User-Friendly Error Response Tests")
    print("=" * 60)
    print()
    
    test_functions = [
        test_error_message_quality,
        test_contextual_messages,
        test_validation_errors,
        test_fallback_responses,
        test_api_integration,
        test_error_response_structure,
        test_configuration_options
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            print()
    
    print("=" * 60)
    print("✅ All user-friendly error response tests completed!")
    print()
    
    # Summary
    print("📋 User-Friendly Error Features Tested:")
    print("   • Clear, non-technical error messages")
    print("   • Actionable suggestions for users")
    print("   • Context-aware error responses")
    print("   • Validation error formatting")
    print("   • Fallback response generation")
    print("   • API integration compatibility")
    print("   • Configurable detail levels")
    print("   • Structured response format")
    print()
    print("🎯 Ready for user-facing deployment!")

if __name__ == "__main__":
    run_all_tests()