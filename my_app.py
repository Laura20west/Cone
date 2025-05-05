from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
from spacy.tokens import Doc
from spacy.language import Language
import json
from datetime import datetime
from pathlib import Path
import uuid
import random
from collections import defaultdict, deque, Counter
import nltk
from nltk.corpus import wordnet as wn
from typing import Dict, List, Optional, Tuple
import re
from textblob import TextBlob  # For sentiment analysis

# Custom spaCy pipeline component for emotion detection
@Language.component("emotion_detector")
def emotion_detector(doc):
    # Simple emotion detection based on keywords and sentiment
    emotions = {
        'happy': {'keywords': ['happy', 'joy', 'excited', 'great', 'wonderful'], 'score': 0},
        'sad': {'keywords': ['sad', 'depressed', 'unhappy', 'miserable', 'cry'], 'score': 0},
        'angry': {'keywords': ['angry', 'mad', 'furious', 'hate', 'annoyed'], 'score': 0},
        'neutral': {'keywords': [], 'score': 0}
    }
    
    # Count keyword matches
    for token in doc:
        for emotion, data in emotions.items():
            if token.text.lower() in data['keywords']:
                data['score'] += 1
    
    # Add sentiment analysis
    sentiment = TextBlob(doc.text).sentiment.polarity
    if sentiment > 0.3:
        emotions['happy']['score'] += 2
    elif sentiment < -0.3:
        emotions['sad']['score'] += 2
    
    # Determine dominant emotion
    dominant_emotion = max(emotions.items(), key=lambda x: x[1]['score'])[0]
    doc._.emotion = dominant_emotion
    doc._.sentiment = sentiment
    
    return doc

# Initialize NLP with custom pipeline
nlp = spacy.load("en_core_web_md")
nlp.add_pipe("emotion_detector", last=True)
Doc.set_extension("emotion", default="neutral")
Doc.set_extension("sentiment", default=0.0)
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

app = FastAPI()

# Configuration
DATASET_PATH = Path("conversation_dataset.jsonl")
UNCERTAIN_PATH = Path("uncertain_responses.jsonl")
REPLY_POOLS_PATH = Path("reply_pools_augmented.json")
USED_RESPONSES_PATH = Path("used_responses.json")

# Load or initialize reply pools with emotion support
if REPLY_POOLS_PATH.exists():
    with open(REPLY_POOLS_PATH, "r") as f:
        REPLY_POOLS = json.load(f)
    # Ensure all categories have required fields
    for category in REPLY_POOLS.values():
        category.setdefault("triggers", [])
        category.setdefault("responses", defaultdict(list))
        category.setdefault("questions", defaultdict(list))
else:
    REPLY_POOLS = {
        "general": {
            "triggers": [],
            "responses": {
                "neutral": ["Honey, let's talk about something more exciting..."],
                "happy": ["I love your energy! Tell me more..."],
                "sad": ["I'm here for you, baby. What's troubling you?"],
                "angry": ["Let's calm down and talk about this..."]
            },
            "questions": {
                "neutral": ["What really gets you going?"],
                "happy": ["What's making you so happy today?"],
                "sad": ["Do you want to talk about what's bothering you?"],
                "angry": ["What can I do to make things better?"]
            }
        }
    }

# Initialize response tracking
if USED_RESPONSES_PATH.exists():
    with open(USED_RESPONSES_PATH, "r") as f:
        USED_RESPONSES = json.load(f)
else:
    USED_RESPONSES = defaultdict(dict)

# Initialize response queues with emotion support
CATEGORY_QUEUES = {}
for category, data in REPLY_POOLS.items():
    CATEGORY_QUEUES[category] = {}
    for emotion in ["neutral", "happy", "sad", "angry"]:
        responses = data["responses"].get(emotion, [])
        questions = data["questions"].get(emotion, [])
        combinations = [(r_idx, q_idx) for r_idx in range(len(responses)) 
                       for q_idx in range(len(questions))]
        random.shuffle(combinations)
        CATEGORY_QUEUES[category][emotion] = deque(combinations)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class UserMessage(BaseModel):
    message: str
    context: Optional[Dict] = None

class SallyResponse(BaseModel):
    matched_word: str
    matched_category: str
    confidence: float
    emotion: str
    sentiment: float
    replies: List[str]

def log_to_dataset(user_input: str, response_data: dict):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user_input": user_input,
        "matched_category": response_data["matched_category"],
        "emotion": response_data.get("emotion", "neutral"),
        "sentiment": response_data.get("sentiment", 0.0),
        "response": response_data["replies"][0] if response_data["replies"] else None,
        "question": response_data["replies"][1] if len(response_data["replies"]) > 1 else None,
        "confidence": response_data["confidence"],
        "embedding": nlp(user_input).vector.tolist()
    }
    
    with open(DATASET_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def store_uncertain(user_input: str):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user_input": user_input,
        "reviewed": False
    }
    
    with open(UNCERTAIN_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def track_used_response(category: str, emotion: str, response_idx: int, question_idx: int):
    if category not in USED_RESPONSES:
        USED_RESPONSES[category] = {}
    if emotion not in USED_RESPONSES[category]:
        USED_RESPONSES[category][emotion] = {"responses": [], "questions": []}
    
    USED_RESPONSES[category][emotion]["responses"].append(response_idx)
    USED_RESPONSES[category][emotion]["questions"].append(question_idx)
    
    with open(USED_RESPONSES_PATH, "w") as f:
        json.dump(USED_RESPONSES, f, indent=2)

def get_fresh_response_pair(category: str, emotion: str) -> Tuple[int, int]:
    """Get a response pair that hasn't been used recently"""
    category_data = REPLY_POOLS[category]
    responses = category_data["responses"].get(emotion, [])
    questions = category_data["questions"].get(emotion, [])
    
    if not responses or not questions:
        return (0, 0)  # Fallback to first pair
    
    # Get all possible combinations
    all_combinations = [(r_idx, q_idx) for r_idx in range(len(responses))
                       for q_idx in range(len(questions))]
    
    # Filter out recently used combinations
    used_responses = USED_RESPONSES.get(category, {}).get(emotion, {}).get("responses", [])
    used_questions = USED_RESPONSES.get(category, {}).get(emotion, {}).get("questions", [])
    
    available_combinations = [
        (r, q) for r, q in all_combinations
        if r not in used_responses[-10:] and q not in used_questions[-10:]
    ]
    
    if available_combinations:
        return random.choice(available_combinations)
    else:
        # If all have been used recently, reset tracking for this category+emotion
        if category in USED_RESPONSES and emotion in USED_RESPONSES[category]:
            USED_RESPONSES[category][emotion] = {"responses": [], "questions": []}
        return random.choice(all_combinations)

def extract_implicit_triggers(doc) -> List[Tuple[str, float]]:
    """Find potential triggers not in our explicit list"""
    triggers = []
    
    # Look for nouns and verbs that might be relevant
    for token in doc:
        if token.pos_ in ["NOUN", "VERB"] and not token.is_stop:
            # Check if similar to any existing triggers
            for category, data in REPLY_POOLS.items():
                for known_trigger in data["triggers"]:
                    known_doc = nlp(known_trigger)
                    similarity = token.similarity(known_doc)
                    if similarity > 0.7:
                        triggers.append((token.text, similarity))
    
    # Look for phrases that match common patterns
    noun_chunks = list(doc.noun_chunks)
    for chunk in noun_chunks:
        chunk_text = chunk.text.lower()
        if len(chunk_text.split()) > 1:  # Multi-word phrases only
            for category, data in REPLY_POOLS.items():
                for known_trigger in data["triggers"]:
                    if known_trigger in chunk_text or chunk_text in known_trigger:
                        triggers.append((chunk_text, 0.8))
    
    return triggers

@app.post("/1A9I6F1O5R1C8O3N87E5145ID", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    message = user_input.message.strip()
    doc = nlp(message.lower())
    emotion = doc._.emotion
    sentiment = doc._.sentiment
    
    # Enhanced matching with implicit triggers
    best_match = ("general", None, 0.0)
    
    # 1. First check explicit triggers
    for category, data in REPLY_POOLS.items():
        for trigger in data["triggers"]:
            trigger_doc = nlp(trigger)
            similarity = doc.similarity(trigger_doc)
            if similarity > best_match[2]:
                best_match = (category, trigger, similarity)
    
    # 2. Check for implicit triggers (words/phrases similar to known triggers)
    implicit_triggers = extract_implicit_triggers(doc)
    for trigger, similarity in implicit_triggers:
        for category, data in REPLY_POOLS.items():
            if similarity > best_match[2]:
                best_match = (category, trigger, similarity)
    
    # 3. Word-based fallback with POS filtering
    for token in doc:
        if token.pos_ in ["NOUN", "VERB"] and not token.is_stop:
            for category, data in REPLY_POOLS.items():
                if token.text in data["triggers"] and best_match[2] < 0.7:
                    best_match = (category, token.text, 0.8)
    
    # Prepare response with emotion context
    response = {
        "matched_word": best_match[1] or "general",
        "matched_category": best_match[0],
        "confidence": round(best_match[2], 2),
        "emotion": emotion,
        "sentiment": round(sentiment, 2),
        "replies": []
    }
    
    # Get fresh response pair based on emotion
    category_data = REPLY_POOLS[best_match[0]]
    emotion_responses = category_data["responses"].get(emotion, category_data["responses"].get("neutral", []))
    emotion_questions = category_data["questions"].get(emotion, category_data["questions"].get("neutral", []))
    
    if emotion_responses and emotion_questions:
        r_idx, q_idx = get_fresh_response_pair(best_match[0], emotion)
        response["replies"].append(emotion_responses[r_idx])
        response["replies"].append(emotion_questions[q_idx])
        track_used_response(best_match[0], emotion, r_idx, q_idx)
    
    # Fallback if no responses found
    if not response["replies"]:
        neutral_responses = REPLY_POOLS["general"]["responses"]["neutral"]
        neutral_questions = REPLY_POOLS["general"]["questions"]["neutral"]
        if neutral_responses and neutral_questions:
            r_idx, q_idx = get_fresh_response_pair("general", "neutral")
            response["replies"].append(neutral_responses[r_idx])
            response["replies"].append(neutral_questions[q_idx])
        else:
            response["replies"] = [
                "I'd love to hear more about that...",
                "Can you tell me more about what's on your mind?"
            ]
    
    # Log interaction
    log_to_dataset(message, response)
    
    # Active learning for uncertain responses
    if response["confidence"] < 0.6:
        store_uncertain(message)
        if len(response["replies"]) > 1:
            response["replies"][1] += " Could you tell me more about that?"
    
    return response

# ... (keep the existing /dataset/analytics and /augment endpoints) ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
