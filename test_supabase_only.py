"""
Simple test script to verify Supabase connection and data.
"""

import requests
from config import SUPABASE_URL, SUPABASE_KEY

def test_supabase_connection():
    """Test basic Supabase connection and data retrieval."""
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Testing Supabase connection...")
    
    try:
        # Test questions table
        url = f"{SUPABASE_URL}/rest/v1/questions?select=count"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            questions_count = len(response.json())
            print(f"✅ Questions table: {questions_count} rows")
            
            # Show sample question
            url = f"{SUPABASE_URL}/rest/v1/questions?limit=1"
            response = requests.get(url, headers=headers)
            if response.json():
                sample = response.json()[0]
                print(f"   Sample: {sample['question_text'][:50]}...")
        else:
            print(f"❌ Questions table error: {response.status_code}")
            return False
        
        # Test responses table
        url = f"{SUPABASE_URL}/rest/v1/responses?select=count"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            responses_count = len(response.json())
            print(f"✅ Responses table: {responses_count} rows")
            
            # Show sample response
            url = f"{SUPABASE_URL}/rest/v1/responses?limit=1"
            response = requests.get(url, headers=headers)
            if response.json():
                sample = response.json()[0]
                print(f"   Sample: {sample['response_value'][:50]}...")
        else:
            print(f"❌ Responses table error: {response.status_code}")
            return False
            
        # Test join query
        url = f"{SUPABASE_URL}/rest/v1/responses?select=*,questions(*)&limit=1"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200 and response.json():
            print("✅ Table relationships working")
            sample = response.json()[0]
            print(f"   Participant: {sample['age_group']} {sample['gender']} from {sample['charity_name']}")
        else:
            print("⚠️  Table relationships may need setup")
            
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def main():
    print("Impact Intelligence Platform - Supabase Test")
    print("=" * 50)
    
    if test_supabase_connection():
        print("\n🎉 Supabase is working perfectly!")
        print("\nYour data is ready. Next steps:")
        print("1. Get Google AI API key: https://makersuite.google.com/app/apikey")
        print("2. Add it to .env file: GOOGLE_API_KEY=your_key_here")
        print("3. Test the full system")
        
        print("\nSample queries you can try:")
        print('- "How do creative programs build resilience?"')
        print('- "What impact does Palace for Life have?"')
        print('- "Show me stories about overcoming challenges"')
    else:
        print("\n❌ There are issues with the Supabase setup.")

if __name__ == "__main__":
    main()