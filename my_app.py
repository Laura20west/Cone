from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
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

# Initialize NLP with larger model for better contextual understanding
try:
    nlp = spacy.load("en_core_web_lg")  # Using larger model for better accuracy
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_lg"])
    nlp = spacy.load("en_core_web_lg")

nltk.download('wordnet')
nltk.download('punkt')

app = FastAPI()

# Configuration
DATASET_PATH = Path("conversation_dataset.jsonl")
UNCERTAIN_PATH = Path("uncertain_responses.jsonl")
REPLY_POOLS_PATH = Path("reply_pools_augmented.json")

# Enhanced reply pool structure with context patterns
DEFAULT_REPLY_POOLS = {
    "general": {
        "triggers": [],
        "context_patterns": [
            {"pattern": ".*", "weight": 1.0}  # Catch-all pattern
        ],
        "responses": ["Honey, let's talk about something more exciting..."],
        "questions": ["What really gets you going?"]
    },
    "romantic": {
        "triggers": ["love", "kiss", "romance", "date", "darling"],
        "context_patterns": [
            {"pattern": ".*(love|adore|miss).*you.*", "weight": 1.5},
            {"pattern": ".*(date|romantic|dinner).*", "weight": 1.3}
        ],
        "responses": ["You make my heart flutter...", "I've been thinking about you all day..."],
        "questions": ["When can I see you again?", "What's your idea of a perfect date?"]
    },
    "intimate": {
        "triggers": ["bed", "touch", "night", "body", "fantasy"],
        "context_patterns": [
            {"pattern": ".*(bed|sleep|tonight).*", "weight": 1.4},
            {"pattern": ".*(touch|feel|body).*", "weight": 1.6}
        ],
        "responses": ["I can't stop thinking about your touch...", "You're driving me wild..."],
        "questions": ["What's your deepest fantasy?", "How do you like to be touched?"]
    }
}

# Load or initialize reply pools
if REPLY_POOLS_PATH.exists():
    with open(REPLY_POOLS_PATH, "r") as f:
        REPLY_POOLS = json.load(f)
    # Ensure all categories have required fields
    for category, data in REPLY_POOLS.items():
        data.setdefault("triggers", [])
        data.setdefault("context_patterns", [{"pattern": ".*", "weight": 1.0}])
        data.setdefault("responses", [])
        data.setdefault("questions", [])
else:
    REPLY_POOLS = DEFAULT_REPLY_POOLS

# Initialize response queues
CATEGORY_QUEUES = {}
for category, data in REPLY_POOLS.items():
    responses = data["responses"]
    questions = data["questions"]
    combinations = [(r_idx, q_idx) for r_idx in range(len(responses)) 
                   for q_idx in range(len(questions))]
    random.shuffle(combinations)
    CATEGORY_QUEUES[category] = deque(combinations)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class UserMessage(BaseModel):
    message: str

class SallyResponse(BaseModel):
    matched_word: Optional[str]
    matched_pattern: Optional[str]
    matched_category: str
    confidence: float
    replies: List[str]

def log_to_dataset(user_input: str, response_data: dict):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user_input": user_input,
        "matched_category": response_data["matched_category"],
        "matched_word": response_data.get("matched_word"),
        "matched_pattern": response_data.get("matched_pattern"),
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

def preprocess_text(text: str) -> str:
    """Clean and normalize text for better matching"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text

def get_contextual_match(message: str, doc) -> Tuple[str, float, Optional[str], Optional[str]]:
    """
    Enhanced matching that combines:
    1. Trigger word matching
    2. Context pattern matching
    3. Semantic similarity
    Returns (best_category, best_score, matched_word, matched_pattern)
    """
    best_category = "general"
    best_score = 0.0
    matched_word = None
    matched_pattern = None
    
    preprocessed = preprocess_text(message)
    
    # Check against all categories
    for category, data in REPLY_POOLS.items():
        # 1. Check trigger words
        for trigger in data["triggers"]:
            if trigger in preprocessed.split():
                score = 0.8  # Base score for word match
                # Boost score if word is important in the sentence
                for token in doc:
                    if token.text == trigger and (token.pos_ in ["NOUN", "VERB", "ADJ"]):
                        score = 0.9
                        break
                if score > best_score:
                    best_score = score
                    best_category = category
                    matched_word = trigger
                    matched_pattern = None
        
        # 2. Check context patterns
        for pattern_data in data.get("context_patterns", []):
            pattern = pattern_data["pattern"]
            weight = pattern_data.get("weight", 1.0)
            if re.fullmatch(pattern, message, re.IGNORECASE):
                score = 1.0 * weight  # Full match with pattern weight
                if score > best_score:
                    best_score = score
                    best_category = category
                    matched_word = None
                    matched_pattern = pattern
        
        # 3. Semantic similarity with triggers (fallback)
        if best_score < 0.7:  # Only use similarity if we don't have a strong match
            for trigger in data["triggers"]:
                trigger_doc = nlp(trigger)
                similarity = doc.similarity(trigger_doc)
                if similarity > 0.7 and similarity > best_score:
                    best_score = similarity
                    best_category = category
                    matched_word = trigger
                    matched_pattern = None
    
    return (best_category, best_score, matched_word, matched_pattern)

@app.post("/1A9I6F1O5R1C8O3N87E5145ID", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    message = user_input.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Empty message")
    
    doc = nlp(message)
    
    # Get best match using enhanced contextual matching
    best_category, best_score, matched_word, matched_pattern = get_contextual_match(message, doc)
    
    # Prepare response
    response = {
        "matched_word": matched_word,
        "matched_pattern": matched_pattern,
        "matched_category": best_category,
        "confidence": round(best_score, 2),
        "replies": []
    }
    
    # Get non-repeating response pair
    category_data = REPLY_POOLS[best_category]
    if category_data["responses"] and category_data["questions"]:
        queue = CATEGORY_QUEUES[best_category]
        
        if not queue:
            # Regenerate combinations if queue is empty
            combinations = [(r_idx, q_idx) for r_idx in range(len(category_data["responses"]))
                           for q_idx in range(len(category_data["questions"]))]
            random.shuffle(combinations)
            queue = deque(combinations)
            CATEGORY_QUEUES[best_category] = queue

        if queue:
            taken = 0
            while taken < 2 and queue:
                r_idx, q_idx = queue.popleft()
                response["replies"].append(category_data["responses"][r_idx])
                response["replies"].append(category_data["questions"][q_idx])
                taken += 1
    
    # Fallback if no responses found
    if not response["replies"]:
        response["replies"] = [
            "Honey, let's take this somewhere more private...",
            "What's your deepest, darkest fantasy?"
        ]
    
    # Log interaction
    log_to_dataset(message, response)
    
    # Active learning for uncertain responses
    if response["confidence"] < 0.6:
        store_uncertain(message)
        if len(response["replies"]) > 1:
            response["replies"][1] += " Could you rephrase that, baby?"
    
    return response

# ... (rest of the file remains the same)
