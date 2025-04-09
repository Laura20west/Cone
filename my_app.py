from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import List, Dict

app = FastAPI()

# CORS setup (allow Tampermonkey to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Data models
class AnalyzeRequest(BaseModel):
    message: str
    session_id: str

class AnalyzeResponse(BaseModel):
    success: bool
    responses: List[str]
    session_id: str

# Response pools (same as before)
RESPONSE_POOLS = {
    "greeting": [
        "Hey hot stuff 💋, ready to have a little chat?",
        "Well hello there, sunshine ☀️! What brings you here today?",
    ],
    "wellbeing": [
        "Sally's doing fabulous as always 😘. How about you, sugar?",
        "Living deliciously, darling 🍓. And you?",
    ],
    # ... other categories ...
}

QUESTION_POOL = [
    "Wanna tell me more? 😉",
    "Can we go deeper on that, baby? 😘",
    # ... other questions ...
]

# Store sessions (in-memory, replace with Redis/DB in production)
sessions: Dict[str, List[dict]] = {}

# API Endpoint
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_message(request: AnalyzeRequest):
    category = _analyze_message(request.message)
    responses = _generate_responses(category, count=2)
    
    # Store session (example)
    if request.session_id not in sessions:
        sessions[request.session_id] = []
    
    sessions[request.session_id].append({
        "message": request.message,
        "category": category,
    })

    return {
        "success": True,
        "responses": responses,
        "session_id": request.session_id,
    }

# Helper functions
def _analyze_message(message: str) -> str:
    KEYWORD_MAP = {
        "greeting": ["hello", "hi", "hey"],
        "wellbeing": ["how", "are", "you"],
        # ... other categories ...
    }
    words = message.lower().split()
    last_match = "general"
    
    for word in words:
        for category, triggers in KEYWORD_MAP.items():
            if word in triggers:
                last_match = category
    return last_match

def _generate_responses(category: str, count: int = 1) -> List[str]:
    responses = []
    for _ in range(count):
        reply = random.choice(RESPONSE_POOLS[category])
        question = random.choice(QUESTION_POOL)
        responses.append(f"{reply} {question}")
    return responses
