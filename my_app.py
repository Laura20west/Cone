from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import Dict, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserMessage(BaseModel):
    message: str

# Combined pools for word matching
KEYWORD_POOLS = {
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
        "Well hello there, sunshine ☀️! What brings you here today?"
    ],
    "wellbeing": [
        "Sally's doing fabulous as always 😘. How about you, sugar?",
        "Feeling spicy today 🌶️. How are you vibing?"
    ],
    "identity": [
        "I'm Sexy Sally, babe 😘. Your digital diva and sweet talker.",
        "They call me Sexy Sally 💄. Want to get to know me better?"
    ],
    "farewell": [
        "Leaving already? I'll miss you, babe 😢",
        "Goodbye, sugar. Come back soon 💋"
    ],
    "assistance": [
        "Of course, darling. Tell Sally what you need 😘",
        "I'm all ears, baby. Let's fix it together 💅"
    ],
    "general": [
        "Hmm, that's a tricky one, honey. Can you give me more? 🤔",
        "Not sure I caught that, sweetheart. Try me again 😘"
    ]
}

QUESTION_POOLS = {
    "greeting": [
        "What's your favorite way to start the day?",
        "Tell me something exciting about your life!"
    ],
    "wellbeing": [
        "What's your current mood?",
        "What's energizing you right now?"
    ],
    "identity": [
        "What would you like to know about me?",
        "How would you describe yourself?"
    ],
    "farewell": [
        "What was your favorite part of our chat?",
        "What are you looking forward to?"
    ],
    "assistance": [
        "What exactly do you need help with?",
        "What have you tried so far?"
    ],
    "general": [
        "Can you elaborate on that?",
        "What else is on your mind?"
    ]
}

def find_matching_category(message: str) -> str:
    words = message.lower().split()
    for word in words:
        for category, keywords in KEYWORD_POOLS.items():
            if word in keywords:
                return category
    return "general"

@app.post("/api/reply")
async def generate_reply(user_message: UserMessage):
    category = find_matching_category(user_message.message)
    
    reply = random.choice(REPLY_POOLS[category])
    question = random.choice(QUESTION_POOLS[category])
    
    return {
        "reply": reply,
        "question": question,
        "full_response": f"{reply}\n{question}",
        "matched_category": category
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
