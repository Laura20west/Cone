from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import Dict, List

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserMessage(BaseModel):
    message: str

# Define keyword triggers and response pools
KEYWORD_MAP = {
    "greeting": ["hello", "hi", "hey"],
    "wellbeing": ["how", "are", "you"],
    "identity": ["your", "name", "who"],
    "farewell": ["bye", "goodbye", "see"],
    "assistance": ["help", "support", "problem"],
    "general": ["what", "when", "why"]
}

REPLY_POOLS = {
    "greeting": [
        "Hey hot stuff 💋, ready to have a little chat?",
        "Well hello there, sunshine ☀️! What brings you here today?",
    ],
    "wellbeing": [
        "Sally's doing fabulous as always 😘. How about you, sugar?",
        "Living deliciously, darling 🍓. And you?",
    ],
    "identity": [
        "I'm Sexy Sally, babe 😘. Your digital diva and sweet talker.",
        "They call me Sexy Sally 💄. Want to get to know me better?",
    ],
    "farewell": [
        "Leaving already? I'll miss you, babe 😢",
        "Goodbye, sugar. Come back soon 💋",
    ],
    "assistance": [
        "Of course, darling. Tell Sally what you need 😘",
        "I'm all ears, baby. Let's fix it together 💅",
    ],
    "general": [
        "Hmm, that's a tricky one, honey. Can you give me more? 🤔",
        "Interesting, babe. Want to dive deeper? 🥽",
    ]
}

QUESTION_POOLS = {
    "greeting": [
        "What's your name, beautiful?",
        "Where are you from, cutie?",
    ],
    "wellbeing": [
        "What made you smile today?",
        "What's your favorite way to relax?",
    ],
    "identity": [
        "What's your favorite color?",
        "What's your zodiac sign?",
    ],
    "farewell": [
        "What was your favorite part of our chat?",
        "When will I see you again?",
    ],
    "assistance": [
        "What exactly do you need help with?",
        "How can I make this better for you?",
    ],
    "general": [
        "Can you tell me more about that?",
        "What else is on your mind?",
    ]
}

def find_last_match(message: str) -> str:
    words = message.lower().split()
    last_match = "general"
    for word in words:
        for category, triggers in KEYWORD_MAP.items():
            if word in triggers:
                last_match = category
    return last_match

@app.post("/api/sexysally")
async def generate_response(user_message: UserMessage):
    category = find_last_match(user_message.message)
    
    reply = random.choice(REPLY_POOLS[category])
    question = random.choice(QUESTION_POOLS[category])
    
    return {
        "category": category,
        "reply": reply,
        "question": question,
        "full_response": f"{reply}\n\n{question}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
