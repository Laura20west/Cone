from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
import json
from datetime import datetime
from pathlib import Path
import uuid
import random
from collections import defaultdict, deque
import nltk
from nltk.corpus import wordnet as wn
from typing import Dict, List, Optional

AUTHORIZED_OPERATORS = {
    "cone478", "cone353", "cone229", "cone516", "cone481", "cone335",
    "cone424", "cone069", "cone096", "cone075", "cone136", "cone406",
    "cone047", "cone461", "cone423", "cone290", "cone407", "cone468",
    "cone221", "cone412", "cone413", "admin@company.com"
}

app = FastAPI()
nlp = spacy.load("en_core_web_md")
nltk.download('wordnet')

# Configuration
DATASET_PATH = Path("conversation_dataset.jsonl")
UNCERTAIN_PATH = Path("uncertain_responses.jsonl")
REPLY_POOLS_PATH = Path("reply_pools_augmented.json")

# Initialize data structures
USED_RESPONSES = defaultdict(set)
USED_QUESTIONS = defaultdict(set)

# Load reply pools
if REPLY_POOLS_PATH.exists():
    with open(REPLY_POOLS_PATH, "r") as f:
        REPLY_POOLS = json.load(f)
else:
    REPLY_POOLS = {
        "general": {
            "triggers": [],
            "responses": ["How can I assist you today?"],
            "questions": ["Could you clarify your request?"]
        }
    }

# Initialize response queues
for category in REPLY_POOLS:
    responses = REPLY_POOLS[category]["responses"]
    questions = REPLY_POOLS[category]["questions"]
    combinations = [(r, q) for r in range(len(responses)) for q in range(len(questions))]
    random.shuffle(combinations)
    REPLY_POOLS[category]["queue"] = deque(combinations)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class VerifyRequest(BaseModel):
    operatorId: str

class ProcessRequest(BaseModel):
    operatorId: str
    message: str
    context: dict

@app.post("/verify")
async def verify_operator(request: VerifyRequest):
    return {"verified": request.operatorId in AUTHORIZED_OPERATORS}

@app.post("/1A9I6F1O5R1C8O3N87E5145ID")
async def process_message(request: ProcessRequest):
    # Authentication
    if request.operatorId not in AUTHORIZED_OPERATORS:
        raise HTTPException(status_code=403, detail="Unauthorized operator")
    
    # NLP Processing
    doc = nlp(request.message.lower())
    best_match = ("general", "general", 0.0)
    
    # Enhanced matching logic
    for category, data in REPLY_POOLS.items():
        for trigger in data["triggers"]:
            trigger_doc = nlp(trigger)
            similarity = doc.similarity(trigger_doc)
            if similarity > best_match[2]:
                best_match = (category, trigger, similarity)
                
        for token in doc:
            if token.pos_ in ["NOUN", "VERB"]:
                for trigger in data["triggers"]:
                    if token.lemma_ in trigger.lower():
                        current_sim = 0.7 + (0.3 * (token.pos_ == "NOUN"))
                        if current_sim > best_match[2]:
                            best_match = (category, token.text, current_sim)
    
    # Generate responses
    category = best_match[0]
    replies = []
    for _ in range(2):  # Generate two response-question pairs
        r_idx, q_idx = get_unique_pair(category)
        if r_idx is not None and q_idx is not None:
            replies.append(REPLY_POOLS[category]["responses"][r_idx])
            replies.append(REPLY_POOLS[category]["questions"][q_idx])
    
    # Fallback responses
    if not replies:
        replies = [
            "Let me find the best solution for you!",
            "Would you like me to look into this further?",
            "Honey, let's take this somewhere more private...",
            "What's your deepest, darkest fantasy?"
        ]
    
    # Log interaction
    log_interaction(request, best_match, replies)
    
    return {
        "matched_word": best_match[1],
        "matched_category": best_match[0],
        "confidence": round(best_match[2], 2),
        "replies": replies
    }

def get_unique_pair(category: str):
    data = REPLY_POOLS.get(category, REPLY_POOLS["general"])
    queue = data["queue"]
    
    if not queue:
        responses = data["responses"]
        questions = data["questions"]
        combinations = [(r, q) for r in range(len(responses)) for q in range(len(questions))]
        random.shuffle(combinations)
        queue = deque(combinations)
        REPLY_POOLS[category]["queue"] = queue
    
    return queue.popleft() if queue else (0, 0)

def log_interaction(request: ProcessRequest, match: tuple, replies: list):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operator": request.operatorId,
        "message": request.message,
        "category": match[0],
        "confidence": match[2],
        "replies": replies,
        "context": request.context
    }
    
    with open(DATASET_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

@app.on_event("startup")
async def startup_tasks():
    augment_dataset()

def augment_dataset():
    # Dataset augmentation logic
    if not DATASET_PATH.exists():
        return
        
    # ... [existing augmentation logic] ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
