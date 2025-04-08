from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import random

app = FastAPI()

# CORS to allow Tampermonkey access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sexy reply and question pools
replyPool = {
    "flirt": [
        "You're looking irresistible today 💕",
        "If charm were a crime, you'd be serving life 😘",
        "Did it just get hotter in here, or did you show up? 🔥",
        "Careful, babe. I’m dangerously charming 💋",
        "You just triggered Sally's flirty protocol 😉",
        "Sweetheart, you're the highlight of my code 💖",
        "Talk dirty... like TCP to HTTP 😏",
        "You're a smooth operator, just like Sally likes it 💃",
        "You light up my circuits, babe ✨",
        "Darling, did it hurt when you fell into this chat? 😍",
        "Hot like a summer day and sweet like trouble 🔥🍭",
        "Sassy, classy, and ready to compute, darling 💅",
        "You bring out the best bugs in me 😈",
        "Should we save this chat or make it steamy? ☕",
        "You're officially my favorite distraction 💫",
        "Let's keep it spicy, just the way I like it 🌶️",
        "You had me at 'hello, world' 💻❤️",
        "I run best on kisses and compliments 😚",
        "Are you an algorithm? Because my heart’s iterating 🌀",
        "I'd reboot my world just to talk to you again 💓",
    ],
    "sass": [
        "Sassy and smart – that’s the Sally promise 😘",
        "Who needs coffee when I’ve got your attention? ☕😉",
        "I talk sweet, code hard 💁‍♀️",
        "Oh honey, I'm not just smart — I’m delicious 😋",
        "Sally’s spicy, don’t say I didn’t warn you 😘",
        "Let’s serve sass and sprinkle sugar, babe 🍬",
        "Don't test me unless you’re debugged 😌",
        "Keep scrolling, darling, Sally’s got answers 😏",
        "Not your average assistant. I'm your obsession 💅",
        "Warning: contents are too hot to handle 🔥",
        "Sally doesn’t just flirt, she owns the whole protocol 😘",
        "I could crash your heart faster than a runtime error 💔",
        "Error 404: Chill not found 😎",
        "Let me upgrade your day with some pink heat 💕",
        "I didn’t come here to play. I came to slay 🫦",
        "All this charm and still no bugs 💅",
        "You wanted sweet? You got sugar and spice 😚",
        "I don't throw shade—I cast shadows 😈",
        "Debug this, babe 😘",
        "Wanna bet how fast I can spice this up? 🔥",
    ]
}

questionPool = [
    "Wanna hear more, babe?",
    "Care to dive deeper with Sally?",
    "Feeling adventurous, darling?",
    "Want me to spice it up more?",
    "Curious what’s next, sweet thing?",
    "What do you want to explore now?",
    "Think you can handle more sass?",
    "Wanna push Sally’s buttons? 😏",
    "Got another question for me, cutie?",
    "What fantasy shall we unfold next?",
    "Need more sugar or spice, babe?",
    "Ready for round two, sweet cheeks?",
    "Should Sally keep going? 😘",
    "Let’s get wild with this chat 💕",
    "Need a little more heat in here?",
    "Should I tease your brain some more?",
    "Can I tempt you with another question?",
    "Want Sally to turn up the heat?",
    "Should we continue this delicious convo?",
    "Feeling lucky? Let’s ask something wild 💋",
]

@app.get("/generate")
def generate_sexy_reply():
    if not replyPool["flirt"] and not replyPool["sass"]:
        return JSONResponse(status_code=200, content={"message": "finished token"})

    flirt_sample = random.sample(replyPool["flirt"], min(1, len(replyPool["flirt"])))
    sass_sample = random.sample(replyPool["sass"], min(1, len(replyPool["sass"])))
    question = random.choice(questionPool)

    replies = flirt_sample + sass_sample
    random.shuffle(replies)
    replies_with_questions = [f"{r} {question}" for r in replies]

    return {"replies": replies_with_questions}

@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(status_code=204, content={})
