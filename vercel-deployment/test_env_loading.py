#!/usr/bin/env python3
"""
Test Environment Variable Loading
Quick test to verify environment variables are loaded correctly
"""
import os
import sys
from pathlib import Path

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    print("🧪 Testing Environment Variable Loading")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(__file__).parent / '.env'
    print(f"📁 .env file exists: {env_file.exists()}")
    print(f"📁 .env file path: {env_file}")
    
    if env_file.exists():
        print(f"📁 .env file size: {env_file.stat().st_size} bytes")
        
        # Read .env file manually
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        print(f"📁 .env file lines: {len(lines)}")
        
        # Show first few lines (without sensitive data)
        print("📁 .env file preview:")
        for i, line in enumerate(lines[:5]):
            if 'API_KEY' not in line:
                print(f"   {i+1}: {line.strip()}")
            else:
                print(f"   {i+1}: {line.split('=')[0]}=***")
    
    print()
    
    # Check environment variables directly
    required_vars = [
        'GOOGLE_API_KEY',
        'PINECONE_API_KEY', 
        'PINECONE_ENVIRONMENT',
        'PINECONE_INDEX_NAME',
        'VECTOR_STORE_TYPE'
    ]
    
    print("🔑 Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var:
                print(f"   ✅ {var}: ***{value[-4:]} (length: {len(value)})")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    print()
    
    # Try loading with python-dotenv if available
    try:
        from dotenv import load_dotenv
        print("📦 python-dotenv available")
        
        # Load .env file
        load_dotenv(env_file)
        print("✅ .env file loaded with python-dotenv")
        
        # Check variables again
        print("\n🔑 Environment Variables (after dotenv):")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if 'API_KEY' in var:
                    print(f"   ✅ {var}: ***{value[-4:]} (length: {len(value)})")
                else:
                    print(f"   ✅ {var}: {value}")
            else:
                print(f"   ❌ {var}: Not set")
                
    except ImportError:
        print("📦 python-dotenv not available - install with: pip install python-dotenv")
    
    print()

def test_vector_client_creation():
    """Test vector client creation with current environment"""
    print("🧪 Testing Vector Client Creation")
    print("=" * 50)
    
    try:
        # Try loading dotenv first
        try:
            from dotenv import load_dotenv
            env_file = Path(__file__).parent / '.env'
            load_dotenv(env_file)
            print("✅ Environment loaded with dotenv")
        except ImportError:
            print("⚠️ python-dotenv not available")
        
        # Import and test vector client
        from vector_client import VectorStoreFactory
        
        print("📦 VectorStoreFactory imported successfully")
        
        # Check configuration
        config = {
            "vector_store_type": os.getenv("VECTOR_STORE_TYPE", "pinecone"),
            "pinecone_api_key": os.getenv("PINECONE_API_KEY"),
            "pinecone_environment": os.getenv("PINECONE_ENVIRONMENT"),
            "pinecone_index_name": os.getenv("PINECONE_INDEX_NAME", "rag-survey-responses"),
            "pinecone_namespace": os.getenv("PINECONE_NAMESPACE", "production")
        }
        
        print("🔧 Configuration:")
        for key, value in config.items():
            if 'api_key' in key and value:
                print(f"   {key}: ***{value[-4:]} (length: {len(value)})")
            else:
                print(f"   {key}: {value}")
        
        # Try creating client
        print("\n🔌 Creating vector store client...")
        client = VectorStoreFactory.create_client(config)
        print("✅ Vector store client created successfully")
        
        # Try health check (this might fail due to invalid keys, but that's expected)
        print("\n🏥 Testing health check...")
        try:
            health = client.health_check()
            print(f"✅ Health check result: {health}")
        except Exception as e:
            print(f"⚠️ Health check failed (expected): {str(e)[:100]}...")
        
    except Exception as e:
        print(f"❌ Vector client creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_env_loading()
    print()
    test_vector_client_creation()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("   • Check if all required environment variables are set")
    print("   • Install python-dotenv if needed: pip install python-dotenv")
    print("   • Verify API keys are valid and have proper permissions")
    print("   • Consider using mock clients for testing without real API calls")