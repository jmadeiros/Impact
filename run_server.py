"""
Development server runner with proper error handling and logging.
"""

import uvicorn
import logging
from config import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY

def validate_environment():
    """Validate that all required environment variables are set."""
    missing = []
    
    if not SUPABASE_URL or SUPABASE_URL == "your_supabase_url_here":
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY or SUPABASE_KEY == "your_supabase_anon_key_here":
        missing.append("SUPABASE_KEY")
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_ai_api_key_here":
        missing.append("GOOGLE_API_KEY")
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease update your .env file with the correct values.")
        return False
    
    print("✅ Environment variables configured")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Impact Intelligence Platform - Starting Server")
    print("=" * 50)
    
    if not validate_environment():
        exit(1)
    
    print("Starting FastAPI server on http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("\nAlternatively, you can run: uvicorn main:app --reload")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )