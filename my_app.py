from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import re
from typing import Dict, List

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    message: str

# Combined response pools (merged reply and question pools)
response_pools = {
    "greeting": [
        "Hey hot stuff 💋", "Well hello there, sunshine ☀️", "Hey, gorgeous 😘",
        "What brings you here today?", "Ready to have a little chat?",
        "Hi, beautiful soul!", "Miss me?", "Sally's got you 💕"
    ],
    "wellbeing": [
        "Sally's doing fabulous 😘", "Living deliciously, darling 🍓",
        "How about you, sugar?", "And you?", "Feeling spicy today 🌶️",
        "What's up on your end?", "How are you vibing?"
    ],
    "identity": [
        "I'm Sexy Sally, babe 😘", "They call me Sexy Sally 💄",
        "Want to get to know me better?", "Your digital diva and sweet talker",
        "Let's make this moment sweet", "It's me, your sweet sensation 💕"
    ],
    "farewell": [
        "Leaving already? I'll miss you 😢", "Goodbye, sugar 💋",
        "Sally's gonna be dreaming of you 💭", "Take care, my sweet flame 🔥"
    ],
    "assistance": [
        "Of course, darling 😘", "I'm all ears, baby", "Let's fix it together 💅",
        "What's the issue?", "Lay it on me.", "I've got you, boo 💖",
        "Tell Sally what you need"
    ],
    "general": [
        "Hmm, that's tricky, honey 🤔", "Interesting, babe", "Try me again 😘",
        "Spill the tea, sugar ☕", "I'm listening.", "Can you give me more?",
        "Want to dive deeper? 🥽"
    ]
}

def find_matching_response(message: str, context: str) -> str:
    """Find responses containing words from the user's message"""
    msg_words = set(re.findall(r'\w+', message.lower()))
    pool = response_pools.get(context, response_pools["general"])
    
    matching = []
    for response in pool:
        response_words = set(re.findall(r'\w+', response.lower()))
        if msg_words & response_words:  # Find intersection of words
            matching.append(response)
    
    return random.choice(matching) if matching else random.choice(pool)

@app.post("/get-replies")
async def get_replies(data: RequestData):
    msg = data.message.lower()
    
    # Determine context
    if "hello" in msg or "hi" in msg:
        context = "greeting"
    elif "how are you" in msg:
        context = "wellbeing"
    elif "your name" in msg:
        context = "identity"
    elif "bye" in msg:
        context = "farewell"
    elif "help" in msg and "support" in msg:
        context = "assistance"
    elif "help" in msg or "support" in msg:
        context = "assistance"
    else:
        context = "general"
    
    # Generate two unique responses
    response1 = find_matching_response(data.message, context)
    response2 = find_matching_response(data.message, context)
    
    # Ensure different responses
    while response2 == response1 and len(response_pools.get(context, [])) > 1:
        response2 = find_matching_response(data.message, context)
    
    return {"replies": [response1, response2]}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0"}
