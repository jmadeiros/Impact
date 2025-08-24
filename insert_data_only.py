"""
Script to insert sample data into existing Supabase tables.
Run this after creating tables manually in the Supabase dashboard.
"""

import requests
import json
from config import SUPABASE_URL, SUPABASE_KEY

# Sample questions data
QUESTIONS_DATA = [
    {
        "question_id": "CX01",
        "outcome_measured": "contextual",
        "question_type": "mcq",
        "question_text": "Thinking about school right now, which of these statements feels most true for you?",
        "mcq_options": {"a": "I enjoy it", "b": "It's difficult", "c": "It isn't for me", "d": "Not in mainstream"}
    },
    {
        "question_id": "CX02",
        "outcome_measured": "contextual",
        "question_type": "mcq",
        "question_text": "When you think about your future after you finish school, how do you generally feel?",
        "mcq_options": {"a": "Excited and confident", "b": "Hopeful", "c": "Worried", "d": "I try not to think about it"}
    },
    {
        "question_id": "DD01",
        "outcome_measured": "agency_and_leadership",
        "question_type": "rating",
        "question_text": "How much do you feel you have a voice in what happens at [Program Name]?",
        "mcq_options": None
    },
    {
        "question_id": "DD02",
        "outcome_measured": "agency_and_leadership",
        "question_type": "mcq",
        "question_text": "What is the best way for your voice to be heard here?",
        "mcq_options": {"a": "Leading a project", "b": "Group discussion", "c": "Talking 1-on-1", "d": "Surveys"}
    },
    {
        "question_id": "DD03",
        "outcome_measured": "agency_and_leadership",
        "question_type": "story",
        "question_text": "Tell us about a time your idea was used, or you got to lead something you were proud of.",
        "mcq_options": None
    },
    {
        "question_id": "DD04",
        "outcome_measured": "community_cohesion",
        "question_type": "rating",
        "question_text": "How much has [Program Name] helped you meet people from different backgrounds?",
        "mcq_options": None
    },
    {
        "question_id": "DD05",
        "outcome_measured": "community_cohesion",
        "question_type": "mcq",
        "question_text": "What is the main thing that helps you make friends here?",
        "mcq_options": {"a": "Working on a team", "b": "Free time to chat", "c": "Shared interest", "d": "Staff encouragement"}
    },
    {
        "question_id": "DD06",
        "outcome_measured": "community_cohesion",
        "question_type": "story",
        "question_text": "Tell us about a new friend you've made here and what you have in common.",
        "mcq_options": None
    },
    {
        "question_id": "DD07",
        "outcome_measured": "health_and_wellbeing",
        "question_type": "rating",
        "question_text": "How much has [Program Name] helped you feel less stressed or worried?",
        "mcq_options": None
    },
    {
        "question_id": "DD08",
        "outcome_measured": "health_and_wellbeing",
        "question_type": "mcq",
        "question_text": "After a session here, how do you usually feel?",
        "mcq_options": {"a": "More energized", "b": "More calm and relaxed", "c": "Happy and positive", "d": "No different"}
    },
    {
        "question_id": "DD09",
        "outcome_measured": "health_and_wellbeing",
        "question_type": "story",
        "question_text": "Tell us about something that happened at [Program Name] that made you smile or feel good.",
        "mcq_options": None
    },
    {
        "question_id": "DD10",
        "outcome_measured": "resilience_and_skills",
        "question_type": "rating",
        "question_text": "How much have the skills you've learned here helped you outside the program?",
        "mcq_options": None
    },
    {
        "question_id": "DD11",
        "outcome_measured": "resilience_and_skills",
        "question_type": "mcq",
        "question_text": "What is the most important type of skill you've developed here?",
        "mcq_options": {"a": "A technical skill", "b": "Teamwork/communication", "c": "Resilience/confidence", "d": "Leadership"}
    },
    {
        "question_id": "DD12",
        "outcome_measured": "resilience_and_skills",
        "question_type": "story",
        "question_text": "Tell us about a time you used a skill you learned here to solve a problem or overcome a challenge.",
        "mcq_options": None
    }
]

# Sample responses data (first 30 for testing)
RESPONSES_DATA = [
    {"response_id": 1, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "CX01", "response_value": "c"},
    {"response_id": 2, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "CX02", "response_value": "c"},
    {"response_id": 3, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD01", "response_value": "5"},
    {"response_id": 4, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD02", "response_value": "a"},
    {"response_id": 5, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD03", "response_value": "We told the staff we wanted to make a film about our estate instead of their idea. It felt like our project, not theirs."},
    {"response_id": 6, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD10", "response_value": "5"},
    {"response_id": 7, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD11", "response_value": "c"},
    {"response_id": 8, "participant_id": "p01", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD12", "response_value": "Our main actor quit the day before the shoot. I was so stressed but we had to rewrite the script overnight. We still got the film made."},
    {"response_id": 9, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "CX01", "response_value": "b"},
    {"response_id": 10, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "CX02", "response_value": "b"},
    {"response_id": 11, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "DD04", "response_value": "5"},
    {"response_id": 12, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "DD05", "response_value": "a"},
    {"response_id": 13, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "DD06", "response_value": "My best mate on the team is from Tulse Hill. We never would have met if it wasn't for football."},
    {"response_id": 14, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "DD07", "response_value": "5"},
    {"response_id": 15, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "DD08", "response_value": "a"},
    {"response_id": 16, "participant_id": "p02", "charity_name": "Palace for Life", "gender": "Male", "age_group": "12-14", "question_id": "DD09", "response_value": "After a training session I'm tired but in a good way. I sleep so much better and feel less stressed about school the next day."},
    {"response_id": 17, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "CX01", "response_value": "d"},
    {"response_id": 18, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "CX02", "response_value": "d"},
    {"response_id": 19, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "DD01", "response_value": "4"},
    {"response_id": 20, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "DD02", "response_value": "b"},
    {"response_id": 21, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "DD03", "response_value": "My idea for the chorus was used in the final track. Everyone listened and said it was good."},
    {"response_id": 22, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "DD07", "response_value": "5"},
    {"response_id": 23, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "DD08", "response_value": "c"},
    {"response_id": 24, "participant_id": "p03", "charity_name": "Symphony Studios", "gender": "Male", "age_group": "15-17", "question_id": "DD09", "response_value": "The best part of the week. After a long week of stress just making music with friends makes everything feel ok."},
    {"response_id": 25, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "CX01", "response_value": "c"},
    {"response_id": 26, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "CX02", "response_value": "c"},
    {"response_id": 27, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD10", "response_value": "5"},
    {"response_id": 28, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD11", "response_value": "c"},
    {"response_id": 29, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD12", "response_value": "I failed my mock exam and felt like a total failure. My mentor helped me make a revision plan and I worked hard every day. I passed the real thing. I learned that failing once doesn't make you a failure."},
    {"response_id": 30, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD01", "response_value": "4"}
]

def insert_data(table_name, data):
    """Insert data into a table via Supabase REST API."""
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Response status: {response.status_code}")
        if response.status_code not in [200, 201]:
            print(f"Response body: {response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print("Impact Intelligence Platform - Insert Sample Data")
    print("=" * 60)
    print("⚠️  Make sure you've created the tables first in Supabase dashboard!")
    print()
    
    # Insert questions
    print("Inserting questions...")
    if insert_data("questions", QUESTIONS_DATA):
        print(f"✅ Inserted {len(QUESTIONS_DATA)} questions")
    else:
        print("❌ Failed to insert questions")
    
    print()
    
    # Insert responses
    print("Inserting responses...")
    if insert_data("responses", RESPONSES_DATA):
        print(f"✅ Inserted {len(RESPONSES_DATA)} responses")
    else:
        print("❌ Failed to insert responses")
    
    print("\n🎉 Data insertion complete!")
    print("\nNext steps:")
    print("1. Get Google AI API key from: https://makersuite.google.com/app/apikey")
    print("2. Add it to your .env file")
    print("3. Run: python3 test_connection.py")

if __name__ == "__main__":
    main()