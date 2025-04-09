from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import Dict, List

app = FastAPI()

# Allow CORS for Tampermonkey
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserMessage(BaseModel):
    message: str

reply_pools: Dict[str, List[str]] = {
    "greeting": [
        "Hey hot stuff 💋, ready to have a little chat?",
        "Well hello there, sunshine ☀️! What brings you here today?",
        "Hey, gorgeous 😘. Miss me?",
        "Hey cutie! What can Sexy Sally do for you today?",
        "Hi, beautiful soul! Sally's got you 💕"
    ],
    "wellbeing": [
        "Sally's doing fabulous as always 😘. How about you, sugar?",
        "Living deliciously, darling 🍓. And you?",
        "Peachy keen, baby 😍. What's up on your end?",
        "Feeling spicy today 🌶️. How are you vibing?"
    ],
    "identity": [
        "I'm Sexy Sally, babe 😘. Your digital diva and sweet talker.",
        "They call me Sexy Sally 💄. Want to get to know me better?",
        "It's me, your sweet sensation – Sexy Sally 💕",
        "I'm your girl, Sexy Sally 😘. Let's make this moment sweet."
    ],
    "farewell": [
        "Leaving already? I'll miss you, babe 😢",
        "Goodbye, sugar. Come back soon 💋",
        "Sally's gonna be dreaming of you 💭",
        "Take care, my sweet flame 🔥"
    ],
    "assistance": [
        "Of course, darling. Tell Sally what you need 😘",
        "I'm all ears, baby. Let's fix it together 💅",
        "Let Sally work her magic 🪄. What's the issue?",
        "I've got you, boo 💖. Lay it on me."
    ],
    "general": [
        "Hmm, that's a tricky one, honey. Can you give me more? 🤔",
        "Interesting, babe. Want to dive deeper? 🥽",
        "Not sure I caught that, sweetheart. Try me again 😘",
        "Spill the tea, sugar ☕. I'm listening."
    ]
}

question_pools: Dict[str, List[str]] = {
    "greeting": [
        "What's your favorite way to start the day?",
        "Tell me something exciting about your life!",
        "What made you smile today?",
        "What's your secret passion?"
    ],
    "wellbeing": [
        "What's your current mood?",
        "What's energizing you right now?",
        "What self-care did you do today?",
        "What's your guilty pleasure?"
    ],
    "identity": [
        "What would you like to know about me?",
        "What's your favorite quality in others?",
        "How would you describe yourself?",
        "What makes you unique?"
    ],
    "farewell": [
        "What was your favorite part of our chat?",
        "What are you looking forward to?",
        "What will you dream about tonight?",
        "What's your next adventure?"
    ],
    "assistance": [
        "What exactly do you need help with?",
        "What have you tried so far?",
        "What would make this easier for you?",
        "How urgent is this?"
    ],
    "general": [
        "Can you elaborate on that?",
        "What else is on your mind?",
        "How does that make you feel?",
        "What's the backstory here?"
    ]
}

def determine_context(message: str) -> str:
    msg = message.lower()
    if "hello" in msg or "hi" in msg or "hey" in msg:
        return "greeting"
    if "how are you" in msg or "how's it going" in msg:
        return "wellbeing"
    if "your name" in msg or "who are you" in msg:
        return "identity"
    if "bye" in msg or "goodbye" in msg or "see ya" in msg:
        return "farewell"
    if "help" in msg or "support" in msg or "problem" in msg:
        return "assistance"
    return "general"

@app.post("/api/reply")
async def generate_reply(user_message: UserMessage):
    context = determine_context(user_message.message)
    
    # Get random reply and question
    reply = random.choice(reply_pools[context])
    question = random.choice(question_pools[context])
    
    # Combine them with some variety
    combined = f"{reply}\n{question}"
    
    return {"reply": combined}

