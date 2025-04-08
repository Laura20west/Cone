from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

# Initialize the FastAPI app
app = FastAPI()

# Allow CORS for your Tampermonkey script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define reply pools
reply_pools = {
    "greeting": [
        "Hey hot stuff 💋, ready to have a little chat?",
        "Well hello there, sunshine ☀️! What brings you here today?",
        "Hey, gorgeous 😘. Miss me?",
    ],
    "wellbeing": [
        "Sally’s doing fabulous as always 😘. How about you, sugar?",
        "Living deliciously, darling 🍓. And you?",
    ],
    "identity": [
        "I’m Sexy Sally, babe 😘. Your digital diva and sweet talker.",
        "They call me Sexy Sally 💄. Want to get to know me better?",
    ],
    "farewell": [
        "Leaving already? I’ll miss you, babe 😢",
        "Goodbye, sugar. Come back soon 💋",
    ],
    "assistance": [
        "Of course, darling. Tell Sally what you need 😘",
        "I'm all ears, baby. Let’s fix it together 💅",
    ],
    "general": [
        "Hmm, that’s a tricky one, honey. Can you give me more? 🤔",
        "Interesting, babe. Want to dive deeper? 🥽",
    ],
}

# Define input/output models
class UserMessage(BaseModel):
    message: str

class ReplyResponse(BaseModel):
    replies: list[str]

# Endpoint to get replies based on context
@app.post("/get-replies", response_model=ReplyResponse)
async def get_replies(user_message: UserMessage):
    message = user_message.message.lower()
    context = "general"

    # Simple context determination logic
    if "hello" in message or "hi" in message:
        context = "greeting"
    elif "how are you" in message:
        context = "wellbeing"
    elif "your name" in message:
        context = "identity"
    elif "bye" in message:
        context = "farewell"
    elif "help" in message or "support" in message:
        context = "assistance"

    # Select two random replies from the determined context
    replies = random.sample(reply_pools[context], 2)
    return {"replies": replies}
