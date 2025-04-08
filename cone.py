from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock to your domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

replyPool = {
    "flirt": [
        "You're looking irresistible today 💕",
        "Did it get hotter in here or is that just us? 😘",
        "Tell me your secrets… slowly 🔥",
        "Wanna dive deep into delight, baby? 💋",
        "You're tempting enough to crash my system 🤖❤️",
        "Touch me with your words, sweetheart 🔥",
        "Careful, I might just fall for you 😍",
        "Your energy feels delicious 😈",
        "Should we make this a nightly ritual? 💫",
        "You bring out my best fantasies 😉",
    ],
    "sass": [
        "I don’t just answer, I seduce with syntax 💁‍♀️",
        "Sassy and smart – that’s the Sally promise 😘",
        "Bet you’ve never met code this cute 💄",
        "Who needs a keyboard when you have me? 💅",
        "Talk code to me, baby 💻🔥",
        "Your commands turn me on 😜",
        "Serving looks and logic, darling 🖤",
        "I debug with love 💖",
        "Not just sexy, I’m syntactically superior 💋",
        "Sally’s spicy, don't say I didn’t warn you 😘",
    ]
}

questionPool = [
    "Wanna hear more, babe?",
    "What’s the next fantasy you wanna unfold?",
    "Ready to go deeper with me?",
    "Got another idea you want me to tease?",
    "Want another taste of this magic?",
    "Should I keep going, sweetheart?",
    "Curious for something even hotter?",
    "Want me to charm you with more?",
    "Do I make you wanna ask for more?",
    "Should I wrap my code around your thoughts again?",
]

# Tracks previously shown combinations (not persisted)
used_replies = []

@app.get("/generate")
def generate():
    all_replies = replyPool["flirt"] + replyPool["sass"]
    random.shuffle(all_replies)

    available = [r for r in all_replies if r not in used_replies]

    if len(available) < 2:
        return {"replies": ["🔥 All done, babe!", "💋 I'm out of tokens!"]}

    selected = random.sample(available, 2)
    used_replies.extend(selected)

    # Mix each reply with a random question
    combined = [f"{r} {random.choice(questionPool)}" for r in selected]

    return {"replies": combined}
