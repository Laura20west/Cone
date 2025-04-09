from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import Dict, List

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced reply pools with word triggers
REPLY_POOLS: Dict[str, Dict] = {
    "greeting": {
        "triggers": ["hello", "hi", "hey", "hola", "greetings"],
        "responses": [
            "Hey hot stuff 💋, ready to have a little chat?",
            "Well hello there, sunshine ☀️! What brings you here today?",
            "Hey, gorgeous 😘. Miss me?",
        ]
    },
    "wellbeing": {
        "triggers": ["how", "are", "you", "feeling", "doing"],
        "responses": [
            "Sally's doing fabulous as always 😘. How about you, sugar?",
            "Living deliciously, darling 🍓. And you?",
        ]
    },
    "identity": {
        "triggers": ["your", "name", "who", "are", "you"],
        "responses": [
            "I'm Sexy Sally, babe 😘. Your digital diva and sweet talker.",
            "They call me Sexy Sally 💄. Want to get to know me better?",
        ]
    },
    # ... other categories ...
}

QUESTION_POOL = [
    "Wanna tell me more? 😉",
    "Can we go deeper on that, baby? 😘",
    # ... other questions ...
]

class UserMessage(BaseModel):
    message: str

class SallyResponse(BaseModel):
    matched_word: str
    matched_category: str
    replies: List[str]

def find_last_match(message: str) -> tuple:
    """Find the last matching word and its category"""
    words = message.lower().split()
    last_match = ("general", None)  # (category, matched_word)
    
    for word in words:
        for category, data in REPLY_POOLS.items():
            if word in data["triggers"]:
                last_match = (category, word)
    return last_match

@app.post("/analyze", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    message = user_input.message.strip()
    
    # Find the last matching word and category
    matched_category, matched_word = find_last_match(message)
    
    # Generate responses
    responses = [
        f"{random.choice(REPLY_POOLS[matched_category]['responses'])} "
        f"{random.choice(QUESTION_POOL)}"
        for _ in range(2)
    ]
    
    return {
        "matched_word": matched_word or "general",
        "matched_category": matched_category,
        "replies": responses
    }
