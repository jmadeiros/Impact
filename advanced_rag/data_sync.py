"""
Data Synchronization for Advanced RAG Testing
Creates a safe snapshot of production data for experimentation
"""
import os
import sys
sys.path.append('..')

import requests
import json
from typing import List, Dict, Any
from datetime import datetime
from config_advanced import SUPABASE_URL, SUPABASE_KEY

class DataSynchronizer:
    def __init__(self):
        self.source_url = SUPABASE_URL
        self.source_key = SUPABASE_KEY
        self.snapshot_file = "data_snapshot.json"
        self.backup_file = f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    def fetch_production_data(self) -> Dict[str, List[Dict]]:
        """Fetch current production data safely"""
        print("📥 Fetching production data snapshot...")
        
        headers = {
            "apikey": self.source_key,
            "Authorization": f"Bearer {self.source_key}",
            "Content-Type": "application/json"
        }
        
        data_snapshot = {}
        
        # Fetch responses first (without join since FK relationship isn't set up)
        print("  Fetching survey responses...")
        responses_url = f"{self.source_url}/rest/v1/responses"
        responses_params = {
            "select": "*"
        }
        
        response = requests.get(responses_url, headers=headers, params=responses_params)
        if response.status_code == 200:
            data_snapshot['responses'] = response.json()
            print(f"  ✅ Fetched {len(data_snapshot['responses'])} responses")
        else:
            print(f"  ❌ Failed to fetch responses: {response.status_code}")
            print(f"  Error details: {response.text}")
            return {}
        
        # Fetch questions separately for reference
        print("  Fetching questions...")
        questions_url = f"{self.source_url}/rest/v1/questions"
        questions_params = {"select": "*"}
        
        response = requests.get(questions_url, headers=headers, params=questions_params)
        if response.status_code == 200:
            data_snapshot['questions'] = response.json()
            print(f"  ✅ Fetched {len(data_snapshot['questions'])} questions")
            
            # Debug: Check structure
            print("  Checking data structure...")
            if data_snapshot['responses']:
                print(f"  Sample response keys: {list(data_snapshot['responses'][0].keys())}")
            if data_snapshot['questions']:
                print(f"  Sample question keys: {list(data_snapshot['questions'][0].keys())}")
            
            # Manually join responses with questions
            print("  Joining responses with questions...")
            # Use the correct ID field name
            id_field = 'question_id' if 'question_id' in data_snapshot['questions'][0] else 'id'
            questions_dict = {q[id_field]: q for q in data_snapshot['questions']}
            
            for response_item in data_snapshot['responses']:
                question_id = response_item.get('question_id')
                if question_id and question_id in questions_dict:
                    response_item['questions'] = questions_dict[question_id]
                else:
                    response_item['questions'] = {}
            
            print(f"  ✅ Joined {len(data_snapshot['responses'])} responses with questions")
        else:
            print(f"  ❌ Failed to fetch questions: {response.status_code}")
            print(f"  Error details: {response.text}")
        
        return data_snapshot
    
    def save_snapshot(self, data: Dict[str, List[Dict]]):
        """Save data snapshot to local file"""
        print(f"💾 Saving data snapshot...")
        
        # Create backup of existing snapshot if it exists
        if os.path.exists(self.snapshot_file):
            os.rename(self.snapshot_file, self.backup_file)
            print(f"  📦 Backed up existing snapshot to {self.backup_file}")
        
        # Save new snapshot
        with open(self.snapshot_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"  ✅ Saved snapshot to {self.snapshot_file}")
        
        # Print summary
        if 'responses' in data:
            print(f"  📊 Snapshot contains {len(data['responses'])} responses")
        if 'questions' in data:
            print(f"  📊 Snapshot contains {len(data['questions'])} questions")
    
    def load_snapshot(self) -> Dict[str, List[Dict]]:
        """Load data snapshot from local file"""
        if not os.path.exists(self.snapshot_file):
            print(f"❌ No snapshot file found: {self.snapshot_file}")
            return {}
        
        print(f"📂 Loading data snapshot from {self.snapshot_file}...")
        
        with open(self.snapshot_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Loaded snapshot with {len(data.get('responses', []))} responses")
        return data
    
    def analyze_data_quality(self, data: Dict[str, List[Dict]]):
        """Analyze the quality and characteristics of the data"""
        print("\n📊 DATA QUALITY ANALYSIS")
        print("-" * 40)
        
        responses = data.get('responses', [])
        questions = data.get('questions', [])
        
        if not responses:
            print("❌ No responses in dataset")
            return
        
        # Response analysis
        story_responses = [r for r in responses if len(r.get('response_value', '')) > 20]
        rating_responses = [r for r in responses if r.get('response_value', '').isdigit()]
        short_responses = [r for r in responses if len(r.get('response_value', '')) <= 20 and not r.get('response_value', '').isdigit()]
        
        print(f"Total responses: {len(responses)}")
        print(f"Story responses (>20 chars): {len(story_responses)} ({len(story_responses)/len(responses)*100:.1f}%)")
        print(f"Rating responses (numeric): {len(rating_responses)} ({len(rating_responses)/len(responses)*100:.1f}%)")
        print(f"Short responses: {len(short_responses)} ({len(short_responses)/len(responses)*100:.1f}%)")
        
        # Organization analysis
        orgs = set(r.get('charity_name', 'Unknown') for r in responses)
        print(f"Organizations: {len(orgs)} - {', '.join(sorted(orgs))}")
        
        # Age group analysis
        ages = set(r.get('age_group', 'Unknown') for r in responses)
        print(f"Age groups: {len(ages)} - {', '.join(sorted(ages))}")
        
        # Question type analysis
        if questions:
            q_types = set(q.get('question_type', 'Unknown') for q in questions)
            print(f"Question types: {len(q_types)} - {', '.join(sorted(q_types))}")
        
        # Rich content analysis
        rich_content_count = sum(1 for r in story_responses if any(keyword in r.get('response_value', '').lower() 
                                                                  for keyword in ['confident', 'friend', 'creative', 'team', 'learn']))
        print(f"Rich thematic content: {rich_content_count} responses ({rich_content_count/len(responses)*100:.1f}%)")
        
        return {
            'total_responses': len(responses),
            'story_responses': len(story_responses),
            'organizations': len(orgs),
            'age_groups': len(ages),
            'rich_content_percentage': rich_content_count/len(responses)*100 if responses else 0
        }
    
    def create_test_subset(self, data: Dict[str, List[Dict]], subset_size: int = 50) -> Dict[str, List[Dict]]:
        """Create a smaller test subset for rapid experimentation"""
        print(f"\n🔬 Creating test subset ({subset_size} responses)...")
        
        responses = data.get('responses', [])
        if len(responses) <= subset_size:
            print(f"  Dataset already small enough ({len(responses)} responses)")
            return data
        
        # Stratified sampling to maintain diversity
        story_responses = [r for r in responses if len(r.get('response_value', '')) > 20]
        other_responses = [r for r in responses if len(r.get('response_value', '')) <= 20]
        
        # Take proportional samples
        story_sample_size = min(int(subset_size * 0.7), len(story_responses))
        other_sample_size = min(subset_size - story_sample_size, len(other_responses))
        
        import random
        random.seed(42)  # Reproducible sampling
        
        sampled_responses = (
            random.sample(story_responses, story_sample_size) +
            random.sample(other_responses, other_sample_size)
        )
        
        subset_data = {
            'responses': sampled_responses,
            'questions': data.get('questions', [])
        }
        
        # Save subset
        subset_file = f"data_subset_{subset_size}.json"
        with open(subset_file, 'w') as f:
            json.dump(subset_data, f, indent=2, default=str)
        
        print(f"  ✅ Created test subset: {subset_file}")
        print(f"  📊 Subset contains {len(sampled_responses)} responses")
        
        return subset_data
    
    def sync_data(self, create_subset: bool = True):
        """Complete data synchronization process"""
        print("🔄 STARTING DATA SYNCHRONIZATION")
        print("=" * 50)
        
        # Fetch fresh data
        data = self.fetch_production_data()
        if not data:
            print("❌ Data synchronization failed")
            return False
        
        # Save snapshot
        self.save_snapshot(data)
        
        # Analyze data quality
        quality_stats = self.analyze_data_quality(data)
        
        # Create test subset if requested
        if create_subset and quality_stats['total_responses'] > 30:
            self.create_test_subset(data, subset_size=30)
        
        print("\n✅ Data synchronization complete!")
        print(f"📁 Main snapshot: {self.snapshot_file}")
        if create_subset:
            print(f"📁 Test subset: data_subset_30.json")
        
        return True

if __name__ == "__main__":
    print("🔄 DATA SYNCHRONIZATION FOR ADVANCED RAG TESTING")
    print("=" * 60)
    print("This script creates a safe snapshot of your production data")
    print("for testing advanced RAG features without risk.")
    print("=" * 60)
    
    syncer = DataSynchronizer()
    
    # Check if snapshot already exists
    if os.path.exists(syncer.snapshot_file):
        print(f"\n📁 Existing snapshot found: {syncer.snapshot_file}")
        choice = input("Create fresh snapshot? (y/n): ").lower()
        if choice != 'y':
            # Just analyze existing data
            existing_data = syncer.load_snapshot()
            if existing_data:
                syncer.analyze_data_quality(existing_data)
            exit()
    
    # Sync data
    success = syncer.sync_data(create_subset=True)
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Use the snapshot for vector store population")
        print("2. Run advanced RAG experiments safely")
        print("3. Compare results without affecting production")
    else:
        print("\n❌ Synchronization failed. Check your connection and credentials.")