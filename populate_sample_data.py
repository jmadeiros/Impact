"""
Script to populate Supabase with sample survey data.
This creates the questions and responses tables with realistic test data.
"""

import asyncio
import logging
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json

logger = logging.getLogger(__name__)

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

# Sample responses data
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
    {"response_id": 30, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD01", "response_value": "4"},
    {"response_id": 31, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD02", "response_value": "c"},
    {"response_id": 32, "participant_id": "p04", "charity_name": "I AM IN ME", "gender": "Female", "age_group": "15-17", "question_id": "DD03", "response_value": "She helps me see my own strengths. I didn't think I was good at anything before, but my mentor showed me how my creativity is a skill."},
    {"response_id": 33, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "CX01", "response_value": "b"},
    {"response_id": 34, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "CX02", "response_value": "a"},
    {"response_id": 35, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "DD10", "response_value": "4"},
    {"response_id": 36, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "DD11", "response_value": "b"},
    {"response_id": 37, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "DD12", "response_value": "I've learned how to communicate with my teammates on the pitch without shouting. You have to work together to get anything done."},
    {"response_id": 38, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "DD04", "response_value": "2"},
    {"response_id": 39, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "DD05", "response_value": "b"},
    {"response_id": 40, "participant_id": "p05", "charity_name": "Palace for Life", "gender": "Female", "age_group": "12-14", "question_id": "DD06", "response_value": "It's hard to make friends when you dont know anyone. a lot of the other girls are already in friendship groups."},
    {"response_id": 41, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "CX01", "response_value": "a"},
    {"response_id": 42, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "CX02", "response_value": "a"},
    {"response_id": 43, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "DD01", "response_value": "4"},
    {"response_id": 44, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "DD02", "response_value": "c"},
    {"response_id": 45, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "DD03", "response_value": "I was nervous to talk in the group but I told the leader my idea for the camera angle 1 on 1 and he said it was brilliant and used it."},
    {"response_id": 46, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "DD04", "response_value": "4"},
    {"response_id": 47, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "DD05", "response_value": "a"},
    {"response_id": 48, "participant_id": "p06", "charity_name": "YCUK", "gender": "Male", "age_group": "12-14", "question_id": "DD06", "response_value": "The boy I was paired with was from another college. We worked well together on the editing."},
    {"response_id": 49, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "CX01", "response_value": "d"},
    {"response_id": 50, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "CX02", "response_value": "c"},
    {"response_id": 51, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "DD07", "response_value": "5"},
    {"response_id": 52, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "DD08", "response_value": "b"},
    {"response_id": 53, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "DD09", "response_value": "When I'm editing a video, my mind goes quiet and I forget all my stress. It's a great escape."},
    {"response_id": 54, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "DD04", "response_value": "4"},
    {"response_id": 55, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "DD05", "response_value": "c"},
    {"response_id": 56, "participant_id": "p07", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "15-17", "question_id": "DD06", "response_value": "The girl I worked with on the keyboards goes to a different school. We bonded over our favourite artists and now we share playlists."},
    {"response_id": 57, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "CX01", "response_value": "d"},
    {"response_id": 58, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "CX02", "response_value": "c"},
    {"response_id": 59, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "DD10", "response_value": "5"},
    {"response_id": 60, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "DD11", "response_value": "c"},
    {"response_id": 61, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "DD12", "response_value": "I used to think I had no skills, but the workshop helped me realise that the stuff I do is valuable. I feel much more confident."},
    {"response_id": 62, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "DD01", "response_value": "5"},
    {"response_id": 63, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "DD02", "response_value": "c"},
    {"response_id": 64, "participant_id": "p08", "charity_name": "Spiral Skills CIC", "gender": "Female", "age_group": "18+", "question_id": "DD03", "response_value": "I spoke to the advisor 1-on-1 and she gave me really specific feedback on my CV. It was so helpful and made me feel like she was really focused on me."},
    {"response_id": 65, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "CX01", "response_value": "c"},
    {"response_id": 66, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "CX02", "response_value": "c"},
    {"response_id": 67, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD04", "response_value": "4"},
    {"response_id": 68, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD05", "response_value": "c"},
    {"response_id": 69, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD06", "response_value": "We all just love football. It doesnt matter where you're from. On the pitch, we're one team."},
    {"response_id": 70, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD10", "response_value": "5"},
    {"response_id": 71, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD11", "response_value": "c"},
    {"response_id": 72, "participant_id": "p09", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD12", "response_value": "Resilience. You get fouled, you get back up. You miss a shot, you try again. Simple."},
    {"response_id": 73, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "CX01", "response_value": "b"},
    {"response_id": 74, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "CX02", "response_value": "b"},
    {"response_id": 75, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "DD01", "response_value": "2"},
    {"response_id": 76, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "DD02", "response_value": "b"},
    {"response_id": 77, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "DD03", "response_value": "not really, i shared an idea for the poster but everyone else wanted to do something different so we just went with that."},
    {"response_id": 78, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "DD07", "response_value": "3"},
    {"response_id": 79, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "DD08", "response_value": "d"},
    {"response_id": 80, "participant_id": "p10", "charity_name": "YCUK", "gender": "Female", "age_group": "12-14", "question_id": "DD09", "response_value": "it was ok"},
    {"response_id": 81, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "CX01", "response_value": "b"},
    {"response_id": 82, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "CX02", "response_value": "b"},
    {"response_id": 83, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "DD10", "response_value": "4"},
    {"response_id": 84, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "DD11", "response_value": "c"},
    {"response_id": 85, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "DD12", "response_value": "He helped me realise that it's okay to feel sad sometimes and that talking about it helps. That's a skill i guess."},
    {"response_id": 86, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "DD07", "response_value": "4"},
    {"response_id": 87, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "DD08", "response_value": "b"},
    {"response_id": 88, "participant_id": "p11", "charity_name": "I AM IN ME", "gender": "Male", "age_group": "12-14", "question_id": "DD09", "response_value": "Just talking to my mentor for an hour a week makes me feel calmer. It's a good place to get worries off my chest."},
    {"response_id": 89, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "CX01", "response_value": "b"},
    {"response_id": 90, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "CX02", "response_value": "b"},
    {"response_id": 91, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD07", "response_value": "5"},
    {"response_id": 92, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD08", "response_value": "a"},
    {"response_id": 93, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD09", "response_value": "Scoring the winning goal for the team. best feeling ever. pure happiness."},
    {"response_id": 94, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD04", "response_value": "5"},
    {"response_id": 95, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD05", "response_value": "a"},
    {"response_id": 96, "participant_id": "p12", "charity_name": "Palace for Life", "gender": "Male", "age_group": "15-17", "question_id": "DD06", "response_value": "You learn to trust people from other areas because you rely on them in a match."},
    {"response_id": 97, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "CX01", "response_value": "c"},
    {"response_id": 98, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "CX02", "response_value": "d"},
    {"response_id": 99, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD01", "response_value": "1"},
    {"response_id": 100, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD02", "response_value": "b"},
    {"response_id": 101, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD03", "response_value": "no one listens to me here. the louder kids just take over."},
    {"response_id": 102, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD10", "response_value": "2"},
    {"response_id": 103, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD11", "response_value": "b"},
    {"response_id": 104, "participant_id": "p13", "charity_name": "YCUK", "gender": "Female", "age_group": "15-17", "question_id": "DD12", "response_value": "It was hard to work as a team when one person talks over everyone."},
    {"response_id": 105, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "CX01", "response_value": "b"},
    {"response_id": 106, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "CX02", "response_value": "b"},
    {"response_id": 107, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "DD04", "response_value": "4"},
    {"response_id": 108, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "DD05", "response_value": "c"},
    {"response_id": 109, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "DD06", "response_value": "The girl I worked with on the keyboards goes to a different school. We bonded over our favourite artists and now we share playlists."},
    {"response_id": 110, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "DD01", "response_value": "4"},
    {"response_id": 111, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "DD02", "response_value": "b"},
    {"response_id": 112, "participant_id": "p14", "charity_name": "Symphony Studios", "gender": "Female", "age_group": "12-14", "question_id": "DD03", "response_value": "My idea for a character's name was chosen. It's a small thing but it feels good."},
    {"response_id": 113, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "CX01", "response_value": "d"},
    {"response_id": 114, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "CX02", "response_value": "a"},
    {"response_id": 115, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "DD01", "response_value": "5"},
    {"response_id": 116, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "DD02", "response_value": "c"},
    {"response_id": 117, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "DD03", "response_value": "I spoke to the advisor 1-on-1 and she gave me really specific feedback on my CV. It was so helpful and made me feel like she was really focused on me."},
    {"response_id": 118, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "DD10", "response_value": "5"},
    {"response_id": 119, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "DD11", "response_value": "a"},
    {"response_id": 120, "participant_id": "p15", "charity_name": "Spiral Skills CIC", "gender": "Male", "age_group": "18+", "question_id": "DD12", "response_value": "I learned how to use LinkedIn properly. I thought it was just for old people lol."}
]

async def create_tables():
    """Create the questions and responses tables if they don't exist."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Create questions table
        questions_table_sql = """
        CREATE TABLE IF NOT EXISTS questions (
            question_id TEXT PRIMARY KEY,
            outcome_measured TEXT NOT NULL,
            question_type TEXT NOT NULL CHECK (question_type IN ('rating', 'mcq', 'story')),
            question_text TEXT NOT NULL,
            mcq_options JSONB
        );
        """
        
        # Create responses table
        responses_table_sql = """
        CREATE TABLE IF NOT EXISTS responses (
            response_id INTEGER PRIMARY KEY,
            participant_id TEXT NOT NULL,
            charity_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age_group TEXT NOT NULL,
            question_id TEXT NOT NULL REFERENCES questions(question_id),
            response_value TEXT NOT NULL,
            thematic_tags TEXT[],
            embedding VECTOR(768),
            tag_confidence FLOAT DEFAULT 0.5,
            human_reviewed BOOLEAN DEFAULT FALSE,
            reviewed_at TIMESTAMP
        );
        """
        
        # Enable pgvector extension
        vector_extension_sql = "CREATE EXTENSION IF NOT EXISTS vector;"
        
        supabase.rpc('exec_sql', {'sql': vector_extension_sql}).execute()
        supabase.rpc('exec_sql', {'sql': questions_table_sql}).execute()
        supabase.rpc('exec_sql', {'sql': responses_table_sql}).execute()
        
        print("✅ Tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False

async def populate_questions():
    """Populate the questions table with sample data."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Clear existing data
        supabase.table("questions").delete().neq("question_id", "").execute()
        
        # Insert questions in batches
        batch_size = 10
        for i in range(0, len(QUESTIONS_DATA), batch_size):
            batch = QUESTIONS_DATA[i:i + batch_size]
            result = supabase.table("questions").insert(batch).execute()
            
        print(f"✅ Inserted {len(QUESTIONS_DATA)} questions")
        return True
        
    except Exception as e:
        print(f"❌ Error populating questions: {str(e)}")
        return False

async def populate_responses():
    """Populate the responses table with sample data."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Clear existing data
        supabase.table("responses").delete().neq("response_id", 0).execute()
        
        # Insert responses in batches
        batch_size = 20
        for i in range(0, len(RESPONSES_DATA), batch_size):
            batch = RESPONSES_DATA[i:i + batch_size]
            result = supabase.table("responses").insert(batch).execute()
            
        print(f"✅ Inserted {len(RESPONSES_DATA)} responses")
        return True
        
    except Exception as e:
        print(f"❌ Error populating responses: {str(e)}")
        return False

async def main():
    """Main function to populate the database with sample data."""
    print("Impact Intelligence Platform - Sample Data Population")
    print("=" * 60)
    
    print("Creating tables...")
    if not await create_tables():
        return
    
    print("\nPopulating questions table...")
    if not await populate_questions():
        return
        
    print("\nPopulating responses table...")
    if not await populate_responses():
        return
    
    print("\n🎉 Sample data population complete!")
    print("\nNext steps:")
    print("1. Run: python setup_database.py (to create vector search functions)")
    print("2. Run: python enrich_data.py (to generate embeddings and tags)")
    print("3. Run: uvicorn main:app --reload (to start the API)")
    
    print(f"\nData summary:")
    print(f"- {len(QUESTIONS_DATA)} questions across 4 outcome areas")
    print(f"- {len(RESPONSES_DATA)} responses from 15 participants")
    print(f"- 5 organizations: YCUK, Palace for Life, Symphony Studios, I AM IN ME, Spiral Skills CIC")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())