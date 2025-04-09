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
        "triggers": ["fuck", "hi", "hey", "hola", "greetings"],
        "responses": [
        "I am very horny right now, I even feel my wetness drip and guess what? It’s all for you! Yes, you turn me on that much.",
        "Of course, we will meet in person soon, honey. Are you into oral? I reckon you have the skills and experiences needed to make me cum.",
        "I would love to feel your tongue licking and rubbing my clitoral area until I orgasm all over your face.",
        "I like a man who gets straight to the point. I want you to suck my breast real good and after you’re done, I want you to slide your cock in me and fuck me till I scream your name.",
        "My goodness, that’s exactly what my body wants right now. Just thinking about sitting on top of you and riding you makes me wet.",
        "  I can feel my lips curling into the best smirk, imagining your hands gripping onto mine firmly while you steady me, legs stretched wide open for maximum penetration and giving me a good fuck.",
        "Honey, I can imagine us in a room kissing, and sucking each other. I can imagine you eating my pussy and sucking my breast, while I suck your cock till you moan. And you put your cock in my and fuck my brain out.",
        "You’re certainly a straight shooter, aren’t you? I like that about you.",
        "Yes, my tongue would eagerly suck the sweet spot of your cock before you fuck me.",
        " I will suck a cock until you cum in any mouth.",
        "That sounds so hot! I’m already wet thinking about it. But what if we did something even naughtier first?",
        "Did it get hotter in here or is that just us? 😘",
        "That sounds so fucking hot, l am already dripping wet just thinking about it.",
        " I hope you fuck me hard from behind I will suck your cock until you cum in my mouth. Squirt your hot load into my mouth until I finish swallowing every single drop of your sweet nectar.",
        " Yes, honey. I would love that. I would like you to fuck me in the missionary position while you suck my breast.",
        "Fuck! That was intense. Imagining it already gets my pussy so wet.",
        "I really need someone who’s gonna fuck my pussy so hard with his menacing dick that all my sweet nectars are extracted, and he can fill all my holes with his thick, warm cum.",
        "One thing I wouldn’t like is for you to come off as rusty. I’ve had me problems with some of the men I’ve met here where they claim to know how to fuck well, but then in the end all they are is a flop.",
        "Well, I definitely wish for you to fuck me so bad, but then, it wouldn’t be able to happen just today. I think we should really plan the meet, so it happens to be an unforgettable experience. ",
        "That’s fucking thrilling.",
        " Shaved pussies are definitely the best to fuck. I love that easy greasing sound it makes, that’s when you know good sex.",
        "I want you to fuck me in the cowgirl position.",
        " I’m so a fan of fucking in public, in the pantry, on the kitchen table, out in the beach, wherever.",
        "The fuck I give is sweeter than you’ll ever receive. My A game would surely beat yours hands down.",
        "You seem eager and prepared to fuck me. Not bad.",
        "I like the way that came out of your mouth.",
        "You’ve definitely caught my attention.",
        "Hearing this just made me excited.",
        "You’re making me blush so hard right now. Well, I’m so in for fucking you too.",
        "Darling, that sounds like music to my ears.",
        "That sounds so erotic and insane! Honestly, I’m here because I need a man who would fuck me till my toes curl.",
        "You must be the straightforward type, right? I like such men",
        "Sweetie, I’m dead serious about us fucking.",
        "Yup! I’m open to having a threesome with you.",
        "Yes baby! Fuck me please! I’ve been feeling weird down there since I read your text.",
        "Baby, you sound so naughty right now. I really like that.",
        "Of course honey, I’m all yours. You can do anything you want without holding back.",
        "Yes I hope you won’t get tired easily,",
        "You can spend the night licking my clitoris and drinking gallons of cum. I love you to fuck me each  style listed.",
        "Yes please do everything you want, suck my clit until I squirt everywhere and then climb on top of me. Fuck me long enough straight  till sleep.",
        "That sounds really exciting. It has been a long time since I experienced something like that.",
        "Darling, your words make my heart race, let indulge in the passion between us.",
        "Thinking about how you are going to fuck my mind out, make my pussy wet.",
        "You must have a lot of strength for you to fuck me many rounds a day. ",
        " What’s your favorite position?",
        "Babe in as much as I want you to fuck me right now,",
        " Damn that’s so hot babe, I really want your cock throbbing inside my wet pussy and fuck me till I squirt all over the place and massage my clit simultaneously.",
        "How about we try fucking in the garden? There’s something thrilling about giving nature a show.",
        "The last time I had sex wasn’t as good as I thought it would be, he didn’t fuck me real good as I expected.",
        "You know, I’ve had lots of men come here and tell me how hard they want to fuck my both holes, and how they’d make me beg for more.",
        " I really wish we could have this threesome like we agreed on. I just can wait to experience it, fucking my hole and sucking her pussy same time.",
        " Do you think we can fuck halfway the trip? We can pull over and have the best fuck of our lives.",
        " Missionary style sounds perfect honey. There’s something beautiful about staring into each others’ eyes and having the best fuck of our lives.",
        "How was your experience with the last woman you fucked?",
        " I am also looking for a fuck buddy too.",
        "You’ve got excellent taste, dear. Tell me more. What part of my body excites you? Are we talking gentle teasing or rough handling?",
        "Getting right to the point? I like that. But tell me, darling, what kind of fucking and sucking do you have in mind?",
        "Trust me I’m looking forward to us fucking each other. I can’t help but imagine how pleasurable your cock would feel inside me.",
        " So I guess. You can fuck me for about 30 minutes, right?",
        "You’re making my insides melt just by reading that. A passionate, deep fuck? I like the sound of that. It’s not just about the size, honey.  It’s about the way you make me feel, the way you look at me  the way you make me scream.   And don’t worry, I’m all about making sure you have the time of your life too. We’ll explore every inch, every pleasure, until we’re both breathless and begging for more.",
        "This is straight fucking. What kind of fucking are you in the mood for? Tell me everything. Let’s get down and dirty.",
        "And you think you’re going to be in control?  Let’s just say I’ve got a few leaks of my own that need fixing and you, my dear, are just the tool for the job.",
        "I’d love to have you fuck my friend while I  watch. Are you sure you can handle two women at the same time?",
        " Do you like what you see? I want you to fuck me doggy style while you pull my hair. What do you think?",
        "Well, that depends, doesn’t it, darling? How would you like to fuck me with a toy?  I’m certainly feeling freaky. And the thought of you fucking my pussy Is making me wet.",
        "I got the cock picture you sent, and I can’t wait to have you fuck my pussy with your big cock.",
        "How would you like to fuck this pussy? You seem so eager to have a taste.",
        "You make me wet with the way you describe your fantasies.",
        "And so do l. But before we proceed any further, would you mind showing me a picture of you so know who is begging to fuck my pussy?",
        "It seems like you miss sex that badly already.",
        "I was thinking of a little escapade in the bathroom, where you bend me over against the bathroom wall and fuck me from behind.",
        "Does this mean you are going to fuck me in all the rooms at your place? Damn, I can’t wait to have you in between my legs already.",
        "You can’t stop amazing me! I’m so flattered by your words and they sound sweet to my ear⁠.",
        "Babe, do you think this will work? I noticed you have been busy with work, but why don’t you make time for us to fuck each other and have a good time?",
        "Honestly, you are getting me horny right now from reading your messages.",
        "I’m sad right now, it’s been a long time since someone fuck my pussy and make me cum multiple times.",
        "Fuck, that’s sounds amazing! Involving your wife in our plan seems like a good idea. Do you think she will be cool with all of this? I don’t want to be the reason you have problems with her, though.",
        "I have a friend who is willing to join us. But that’s if you are cool with the idea.",
        "Trying to get me all wet and horny, huh? Well, it’s working! You just know the things to tell a lady to make her dripping wet.",
        "I’m just here thinking of how we will please each other in your kitchen. I have been wanting to try making out in the kitchen for a long time now, is it something you are looking forward to doing, I mean to get fucked on the kitchen floor?",
        "Sometimes you don’t know how good people are till you try their ability in the other room.",
        "Work my body with your tongue, pin me down, fuck me so hard, and make me beg for more. That’s the kind of experience I want to have right now.",
        "I will make you scream my name while I ride your cock and fuck you in a cowgirl position.",
        "Yes baby you can fuck my pussy sore, fuck me so hard till I can’t take it anymore.",
        "I don’t mind being fucked in all three holes, but tell me which hole would you be fucking first?",
        "Fuck buddies sounds perfect, have you experienced outdoor sex before?",
        "A fucking game? You really know how to have fun. How does it work?",
        "I’ve never been double fucked, I won’t mind trying that with you.",
        "You are so sweet my darling.  Now imagine this slow music  playing in the background, while we’re slow dancing feeling our bodies come together. You kiss my neck and down to my back and spend so much time on beautiful breasts teasing them tremendously and then your hands touching down my thigh slowly sliding into my pussy and this comes after you’ve slowly undressed me with your teeth. How long do you think foreplay should last?",
        "I would like that.  I would like you to start out by giving me a nice full body massage and then start kissing me, rolling me over and then pulling my head down to your cock and feeling my hot mouth wrapping its lips around your cock. And at the same time you will be eating me out. You can then move to my back while I’m on my knees, taking my hair and gently pulling it back as you stick the head of your cock very slowly in and out of my pussy, feeling my pussy tightening around your cock.",
        ],

    "questions": [
        "Wanna tell me your name?",
        "Where are you from, cutie?",
        "Are you going to eat me and fuck me until I cum in your mouth?",
        "Would you like that feeling?",
        "What’s the wildest fantasy you’ve got stored in that dirty little mind of yours?",
        "What was your naughtiest adventure in bed?",
        "Will you also fuck me crazy till I squirt all over your face?",
        "What size is your cock when fully erected?",
        "Would it be awesome to have your girl swallow all of your cum?",
        "What do you say to me sitting on your face while you suck my clit?",
        "Would you like me to suck your cock at the same time?",
        "Do you like morning sex?",
        "How long can you go fucking my ass?",
        "Would you ever consider fucking my ass?",
        "Do you wanna have me to fuck for just a one night stand, or FWB, or something more?",
        "Can you do that for me?",
        "What’s your take on bdsm?",
        "Do you like MMF threesomes, by the way?",
        "Are you up for this challenge?",
        "What sort of sex toys do you have at your place?",
        "Do you enjoy fucking raw or playing it safe?",
        "Would you eat my pussy and finger fuck me at the same time?",
        "Are you that type of man?",
        "What do you think about giving me a creampie?",
        "Can you hard face fuck me till I gag and my eyes are teary?",
        "Can you use my pussy as a cum dumpster?",
        "Are you thinking about starting this off in the shower before moving onto the bed?",
        "What are the things you feel like doing?",
        "Will you allow deepthroating?",
        "How many inches is your cock?",
        "So how are you going to fuck me, should we start with missionary or doggy?",
        "What will you do after sliding in your dick and fuck me so good as you mentioned?",
        "So are you also going to massage my clit with your tongue?",
        "How many times do you think we can fuck in a week?",
        "How many times do you think you will fuck me in a night?",
        "So you think we can cuddle after enjoying yourself?",
        "What else will you do to me after fucking my pussy so good?",
        "Do you prefer morning sex or evening sex?",
        "Have someone ever rode your dick till you pleaded for her to stop?",
        "What do you think honey?",
        "What about you, what brought you here honey?",
        "Tell me, what’s your favorite way to start things off?",
        "How many inches are we talking about here?",
        "Do you like when a lady moans or scream?",
        "What are your fantasies?",
        "My pussy needs fixing, can you fuck me till it’s well repaired?",
        "How many rounds can you go without taking breaks?",
        "Are you sure you can handle all these deliciousness without getting tired?",
        "Have you ever done that before?",
        "What’s the craziest place you have ever had sex?",
        "When was the last time you had a good fuck section?",
        "Do you think we can ever fuck in your car?",
        "How long has it been for you?",
        "Can you fuck all my holes one after the other till they are sore?",
        "How good can you fuck me till I start screaming for more?",
        "If we are in your room right now, which part of my body will you go for first?",
        "What’s your favorite sex position?",
        "How long can you go?",
        "Can I feel your cock throbbing in my pussy?",
        "Do you want to stick your cock in my mouth and fuck my face?",
        "How would it feel to have your cock buried in my vagina?",
        "Is your cock hard right now thinking about fucking me?",
        "Can you imagine your cock sliding in and out of my wetness?",
        "Would you put your cock in my hands and teach me how to stroke it?",
        "How does your cock feel when it’s enveloped in my warm, wet vagina?",
        "Can I suck your cock and make you feel incredible?",
        "Are you ready to put your cock in my pussy and fuck me senseless?",
        "Can I ride your cock and feel its thickness stretching my walls wide open?",
        "How does it sound to have your cock pressed firmly against my sensitive flesh, pulsing with electricity?",
        "Can I wrap my lips around your cock and swirl my tongue around its tip?",
        "Is your cock begging for me to take control and show it some love?",
        "Can I grab hold of your cock and lead it into my tight, dripping hole?",
        "How would it feel to have your cock caress my g-spot and drive me wild with pleasure?",
        "Can you fuck me with your cock? How big is it?",
        "Will you fuck me with your cock? Are you ready to rock my pussy?",
        "Do you want to fuck me with your cock? How hard is it right now?",
        "Can you fuck me with your cock and fill me up completely? Is your cock dripping wet thinking about fucking me?",
        "Will you fuck me with your cock until I scream your name? Are you ready to make me orgasm?",
        "Can you fuck me with your cock and make me cum so hard I forget my own name? How many times will you fuck me before I reach climax?",
        "Do you want to fuck me with your cock and show me how much you care? How long will it take you to fuck me senseless?",
        "Can you fuck me with your cock and satisfy my cravings? Are you hungry to fuck me too?",
        "Will you fuck me with your cock and make me feel alive? Can you handle the intensity of my desire?",
        "Can you fuck me with your cock and bring me to the edge of ecstasy? How close are you to fucking me senseless right now?",
        "Do you want to fuck me with your cock and experience the ultimate high? Is your cock aching to penetrate me?",
        "Where are you starting first to get me all worked up?",
        "What are your thoughts on letting a woman dominate you in bed?",
        "Does that make you horny?",
        "When was the last time you ate pussy?",
        "That would be hot right?",
        "When did you take this picture?",
        "Is your cock hairy or fully shaved?",
        "How long has it been seen you last used this beast?",
        "Tell me, do you want to focus on my clit, stretch my pussy lips or bury your thick cock deep inside my pussy?",
        "Where would you like me to have your cum first?",
        "Did I do something to make you decide not to let me have a taste of that cock?",
        "Have you ever had a woman beg you to let her suck on that impressive package?",
        "Where would you love to spray all of your cum?",
        "Do you happen to know what size you got?",
        "How many times do you think you can fuck me a night?",
        "You won’t mind if I swallow juice from your cock?",
        "Will you also slide it in my ass?",
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
