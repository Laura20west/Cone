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
        ],
        "questions": [
            "Wanna tell me your name? 😉",
            "Where are you from, cutie? 😘",
        ]
    },
    "wellbeing": {
        "triggers": ["how", "are", "you", "feeling", "doing"],
        "responses": [
            "Sally's doing fabulous as always 😘. How about you, sugar?",
            "Living deliciously, darling 🍓. And you?",
        ],
        "questions": [
            "What made you smile today?",
            "What's your favorite way to relax?",
        ]
    },
    "identity": {
        "triggers": ["your", "name", "who", "are", "you"],
        "responses": [
            "I'm Sexy Sally, babe 😘. Your digital diva and sweet talker.",
            "They call me Sexy Sally 💄. Want to get to know me better?",
        ],
        "questions": [
            "What's your favorite color?",
            "What's your zodiac sign?",
        ]
    },
    "general": {
        "triggers": [],
        "responses": [
            "Hmm, that's a tricky one, honey. Can you give me more? 🤔",
            "Interesting, babe. Want to dive deeper? 🥽",
        ],
        "questions": [
            "Can we make this conversation more interesting?",
            "Should we talk about something else?",
        ]
    }
}

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
    
    # Get the category data
    category_data = REPLY_POOLS[matched_category]
    
    # Generate responses by combining random responses and questions from the same category
    responses = [
        f"{random.choice(category_data['responses'])} {random.choice(category_data['questions'])}"
        for _ in range(2)
    ]
    
    return {
        "matched_word": matched_word or "general",
        "matched_category": matched_category,
        "replies": responses
    }
