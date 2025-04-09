# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import Dict, List

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    message: str

# Enhanced response pools
reply_pools = {
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
    "cute": [
        "fuck yea.",
        "okay handsome",
        "you're adorable 💖",
        "my sweet angel 😇"
    ],
    "assistance": [
        "How can I help?",
        "What support do you need?",
        "Tell me more about your problem 💭",
        "Let's fix this together ✨"
    ]
}

question_pools = {
    "greeting": [
        "What's your name?",
        "How's your day going?",
    ],
    "wellbeing": [
        "What made you smile today?",
        "Need some positive vibes?",
    ],
    "identity": [
        "What's your favorite color?",
        "What's your zodiac sign?",
    ],
    "cute": [
        "You need a hug?",
        "Want some candy? 🍬",
    ],
    "assistance": [
        "Need more help?",
        "Should I explain differently?",
    ]
}

def determine_context(message: str) -> str:
    msg = message.lower()
    if "help" in msg and "support" in msg: return "cute"
    if "hello" in msg or "hi" in msg: return "greeting"
    if "how are you" in msg: return "wellbeing"
    if "your name" in msg: return "identity"
    if "bye" in msg: return "farewell"
    if "help" in msg or "support" in msg: return "assistance"
    return "general"

def generate_random_response(context: str) -> str:
    """Generate one random response by mixing reply and question"""
    reply = random.choice(reply_pools.get(context, ["Hmm..."]))
    question = random.choice(question_pools.get(context, [""]))
    return f"{reply} {question}".strip() if random.random() > 0.5 else f"{question} {reply}".strip()

@app.post("/get-replies")
async def get_replies(data: RequestData):
    context = determine_context(data.message)
    
    # Generate two completely independent random responses
    response1 = generate_random_response(context)
    response2 = generate_random_response(context)
    
    # Ensure we don't return identical responses
    while response2 == response1:
        response2 = generate_random_response(context)
    
    return {
        "replies": [
            response1,
            response2
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.1.0"}
