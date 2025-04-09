# main.py
from fastapi import FastAPI, HTTPException
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

# Response pools
reply_pools = {
    "greeting": [
        "Hey hot stuff 💋, ready to have a little chat?",
        "Well hello there, sunshine ☀️! What brings you here today?",
        "Hey, gorgeous 😘. Miss me?",
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
    ]
}

question_pools = {
    "greeting": [
        "a?",
        "b?",
    ],
    "wellbeing": [
        "c?",
        "d?",
    ],
    "identity": [
        "e?",
        "f?",
    ],
    "cute": [
        "g?",
        "h?",
    ]
}

def determine_context(message: str) -> str:
    msg = message.lower()
    if "hello" in msg or "hi" in msg: return "greeting"
    if "how are you" in msg: return "wellbeing"
    if "your name" in msg: return "identity"
    if "bye" in msg: return "farewell"
    if "help" in msg or "support" in msg: return "assistance"
    if "help" in msg and "support" in msg: return "cute"
    return "general"

@app.post("/get-replies")
async def get_replies(data: RequestData):
    context = determine_context(data.message)
    
    # Get random reply and question
    reply = random.choice(reply_pools.get(context, ["Hmm, interesting..."]))
    question = random.choice(question_pools.get(context, [""]))
    
    # Mix them randomly
    if random.random() > 0.5:
        response = f"{reply} {question}"
    else:
        response = f"{question} {reply}"
    
    return {
        "replies": [
            response,
            "Alternative reply: " + random.choice(reply_pools.get(context, ["Let's talk more 😘"]))
        ]
    }
