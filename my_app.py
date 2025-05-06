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
from collections import Counter

# Initialize NLP
nlp = spacy.load("en_core_web_md")
nltk.download('wordnet')

app = FastAPI()

# Configuration
DATASET_PATH = Path("conversation_dataset.jsonl")
UNCERTAIN_PATH = Path("uncertain_responses.jsonl")
REPLY_POOLS_PATH = Path("reply_pools_augmented.json")

# Track used responses and questions
USED_RESPONSE_QUESTION_PAIRS = defaultdict(set)
RESET_THRESHOLD = 0.9  # Reset when 90% of combinations are used

# Load or initialize reply pools
if REPLY_POOLS_PATH.exists():
    with open(REPLY_POOLS_PATH, "r") as f:
        REPLY_POOLS = json.load(f)
    # Ensure all categories have required fields
    for category in REPLY_POOLS.values():
        category.setdefault("triggers", [])
        category.setdefault("responses", [])
        category.setdefault("questions", [])
else:
    REPLY_POOLS = {
        "general": {
            "triggers": [],
            "responses": ["Honey, let's talk about something more exciting..."],
            "questions": ["What really gets you going?"]
        }
    }

# Initialize response queues and track total combinations
CATEGORY_COMBINATIONS = {}
for category, data in REPLY_POOLS.items():
    responses = data["responses"]
    questions = data["questions"]
    total_combinations = len(responses) * len(questions)
    CATEGORY_COMBINATIONS[category] = total_combinations

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
    matched_word: str
    matched_category: str
    confidence: float
    replies: List[str]

def log_to_dataset(user_input: str, response_data: dict):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user_input": user_input,
        "matched_category": response_data["matched_category"],
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

def augment_dataset():
    if not DATASET_PATH.exists():
        return
    
    with open(DATASET_PATH, "r") as f:
        entries = [json.loads(line) for line in f]
    
    category_counts = defaultdict(int)
    for entry in entries:
        category_counts[entry["matched_category"]] += 1
    
    avg_count = sum(category_counts.values()) / len(category_counts) if category_counts else 0
    needs_augmentation = [k for k, v in category_counts.items() if v < avg_count * 0.5]
    
    for category in needs_augmentation:
        if category not in REPLY_POOLS:
            continue
            
        base_triggers = REPLY_POOLS[category]["triggers"]
        new_triggers = []
        
        for trigger in base_triggers:
            doc = nlp(trigger)
            lemmatized = " ".join([token.lemma_ for token in doc])
            new_triggers.append(lemmatized)
            
            for token in doc:
                if token.pos_ in ["NOUN", "VERB"]:
                    syns = [syn.lemmas()[0].name() for syn in wn.synsets(token.text)]
                    if syns:
                        new_triggers.append(trigger.replace(token.text, syns[0]))
        
        REPLY_POOLS[category]["triggers"] = list(set(REPLY_POOLS[category]["triggers"] + new_triggers))
    
    with open(REPLY_POOLS_PATH, "w") as f:
        json.dump(REPLY_POOLS, f, indent=2)
    
    # Update combinations count after augmentation
    global CATEGORY_COMBINATIONS
    for category, data in REPLY_POOLS.items():
        responses = data["responses"]
        questions = data["questions"]
        CATEGORY_COMBINATIONS[category] = len(responses) * len(questions)

def get_best_match(doc):
    best_match = ("general", None, 0.0)
    
    for category, data in REPLY_POOLS.items():
        for trigger in data["triggers"]:
            trigger_doc = nlp(trigger)
            similarity = doc.similarity(trigger_doc)
            if similarity > best_match[2]:
                best_match = (category, trigger, similarity)
        
        for token in doc:
            if token.pos_ in ["NOUN", "VERB", "ADJ"]:
                for trigger in data["triggers"]:
                    if token.lemma_ in trigger.lower():
                        current_sim = 0.7 + (0.3 * (token.pos_ == "NOUN"))
                        if current_sim > best_match[2]:
                            best_match = (category, token.text, current_sim)
    
    if best_match[2] < 0.7:
        for token in doc:
            if token.pos_ in ["NOUN", "VERB"]:
                synsets = wn.synsets(token.text)
                for syn in synsets:
                    for lemma in syn.lemmas():
                        for category, data in REPLY_POOLS.items():
                            if lemma.name() in data["triggers"]:
                                current_sim = 0.65
                                if current_sim > best_match[2]:
                                    best_match = (category, lemma.name(), current_sim)
    
    return best_match

def get_unique_response_pair(category):
    if category not in REPLY_POOLS:
        return (None, None)
        
    category_data = REPLY_POOLS[category]
    responses = category_data["responses"]
    questions = category_data["questions"]
    
    # Check if we need to reset used pairs
    total_combinations = CATEGORY_COMBINATIONS.get(category, 1)
    used_count = len(USED_RESPONSE_QUESTION_PAIRS[category])
    
    if used_count > 0 and (used_count / total_combinations) >= RESET_THRESHOLD:
        USED_RESPONSE_QUESTION_PAIRS[category].clear()
    
    # Generate all possible combinations
    all_combinations = [(r_idx, q_idx) 
                        for r_idx in range(len(responses)) 
                        for q_idx in range(len(questions))]
    
    # Find unused combinations
    available_combinations = [pair for pair in all_combinations 
                            if pair not in USED_RESPONSE_QUESTION_PAIRS[category]]
    
    if available_combinations:
        selected_pair = random.choice(available_combinations)
        USED_RESPONSE_QUESTION_PAIRS[category].add(selected_pair)
        return selected_pair
    else:
        # If all combinations are used (shouldn't happen due to reset threshold)
        USED_RESPONSE_QUESTION_PAIRS[category].clear()
        if all_combinations:
            selected_pair = random.choice(all_combinations)
            USED_RESPONSE_QUESTION_PAIRS[category].add(selected_pair)
            return selected_pair
    
    return (0, 0) if responses and questions else (None, None)

@app.post("/1A9I6F1O5R1C8O3N87E5145ID", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    message = user_input.message.strip()
    doc = nlp(message.lower())
    
    best_match = get_best_match(doc)
    
    response = {
        "matched_word": best_match[1] or "general",
        "matched_category": best_match[0],
        "confidence": round(best_match[2], 2),
        "replies": []
    }
    
    r_idx, q_idx = get_unique_response_pair(best_match[0])
    
    if r_idx is not None and q_idx is not None:
        category_data = REPLY_POOLS[best_match[0]]
        response["replies"].append(category_data["responses"][r_idx])
        response["replies"].append(category_data["questions"][q_idx])
    
    if not response["replies"]:
        response["replies"] = [
            "Honey, let's take this somewhere more private...",
            "What's your deepest, darkest fantasy?"
        ]
    
    log_to_dataset(message, response)
    
    if response["confidence"] < 0.6:
        store_uncertain(message)
        if len(response["replies"]) > 1:
            response["replies"][1] += " Could you rephrase that, baby?"
    
    return response

@app.get("/dataset/analytics")
async def get_analytics():
    analytics = {
        "total_entries": 0,
        "common_categories": {},
        "confidence_stats": {},
        "usage_stats": {}
    }
    
    if DATASET_PATH.exists():
        with open(DATASET_PATH, "r") as f:
            entries = [json.loads(line) for line in f]
        
        analytics["total_entries"] = len(entries)
        analytics["common_categories"] = Counter(entry["matched_category"] for entry in entries)
        
        if entries:
            confidences = [entry["confidence"] for entry in entries]
            analytics["confidence_stats"] = {
                "average": round(sum(confidences)/len(confidences), 2),
                "min": round(min(confidences), 2),
                "max": round(max(confidences), 2)
            }
    
    # Add usage statistics
    analytics["usage_stats"] = {
        category: {
            "used": len(USED_RESPONSE_QUESTION_PAIRS[category]),
            "total": CATEGORY_COMBINATIONS.get(category, 0)
        }
        for category in REPLY_POOLS.keys()
    }
    
    return analytics

@app.post("/augment")
async def trigger_augmentation():
    augment_dataset()
    return {"status": "Dataset augmented", "new_pools": REPLY_POOLS}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
