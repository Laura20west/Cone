from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize NLP models
try:
    nlp = spacy.load("en_core_web_md")
    grammar_checker = spacy.load("en_core_web_sm")
except Exception as e:
    logger.error(f"Failed to load NLP models: {str(e)}")
    raise

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Complete reply pools with integrated question bank
REPLY_POOLS = {
    "greeting": {
        "triggers": ["hi", "hello", "hey", "hola"],
        "responses": [
            {"text": "Hello there beautiful", "pos": {"VERB": ["Hello"], "ADJ": ["beautiful"]}},
            {"text": "Hi sexy", "pos": {"VERB": ["Hi"], "ADJ": ["sexy"]}},
            {"text": "Hey hot stuff", "pos": {"VERB": ["Hey"], "ADJ": ["hot"]}}
        ],
        "questions": [
            {"text": "How are you doing today?", "pos": {"ADV": ["How"], "VERB": ["are", "doing"]}},
            {"text": "What's your lovely name?", "pos": {"NOUN": ["name"], "ADJ": ["lovely"]}},
            {"text": "How can I please you?", "pos": {"VERB": ["can", "please"], "PRON": ["I", "you"]}}
        ]
    },
    "explicit": {
        "triggers": ["fuck", "sex", "dick", "pussy", "cock", "hard"],
        "responses": [
            {"text": "I want your hard cock inside me", "pos": {"VERB": ["want"], "ADJ": ["hard"], "NOUN": ["cock"]}},
            {"text": "My wet pussy is ready for you", "pos": {"ADJ": ["wet"], "NOUN": ["pussy"], "VERB": ["is"]}},
            {"text": "Fuck me harder daddy", "pos": {"VERB": ["Fuck"], "ADV": ["harder"], "NOUN": ["daddy"]}}
        ],
        "questions": [
            {"text": "How big is your thick dick?", "pos": {"ADJ": ["big", "thick"], "NOUN": ["dick"]}},
            {"text": "Where do you want to cum?", "pos": {"VERB": ["do", "want", "cum"], "PRON": ["you"]}},
            {"text": "Can you handle my tight body?", "pos": {"VERB": ["Can", "handle"], "ADJ": ["tight"], "NOUN": ["body"]}}
        ]
    }
}

def preprocess_pos_tags():
    """Ensure all entries have detailed POS tags with error handling"""
    try:
        for category in REPLY_POOLS.values():
            for item in category["responses"] + category["questions"]:
                if "pos" not in item:
                    doc = nlp(item["text"])
                    pos_tags = defaultdict(list)
                    for token in doc:
                        if not token.is_punct and not token.is_space:
                            pos_tags[token.pos_].append(token.text)
                    item["pos"] = dict(pos_tags)
    except Exception as e:
        logger.error(f"Error in preprocess_pos_tags: {str(e)}")
        raise

preprocess_pos_tags()

def is_grammatically_correct(text: str) -> bool:
    """Enhanced grammar checking with error handling"""
    try:
        doc = grammar_checker(text)
        has_verb = any(token.pos_ == "VERB" for token in doc)
        has_subject = any(token.pos_ in ["NOUN", "PROPN", "PRON"] for token in doc)
        return has_verb and has_subject
    except Exception as e:
        logger.error(f"Grammar check failed for '{text}': {str(e)}")
        return False

def combine_response_question(response: Dict, question: Dict) -> Tuple[str, bool]:
    """
    Intelligently combine response and question elements
    Returns tuple of (combined_text, was_mixed_successfully)
    """
    try:
        combined_pos = {
            "VERB": response["pos"].get("VERB", []) + question["pos"].get("VERB", []),
            "NOUN": response["pos"].get("NOUN", []) + question["pos"].get("NOUN", []),
            "ADJ": response["pos"].get("ADJ", []) + question["pos"].get("ADJ", []),
            "ADV": response["pos"].get("ADV", []) + question["pos"].get("ADV", []),
            "PRON": response["pos"].get("PRON", []) + question["pos"].get("PRON", [])
        }

        templates = [
            "{VERB} {PRON} {ADV}",
            "{PRON} {VERB} your {ADJ} {NOUN}",
            "Let's {VERB} {ADV}",
            "How {ADJ} is your {NOUN}?",
            "Where {VERB} {PRON} {ADV}?",
            "Can {PRON} {VERB} my {ADJ} {NOUN}?"
        ]

        for _ in range(10):  # Multiple attempts
            template = random.choice(templates)
            required_pos = set(template.split("}")[0].split("{")[1:])
            
            if all(combined_pos.get(pos, []) for pos in required_pos):
                try:
                    filled = template.format(
                        VERB=random.choice(combined_pos["VERB"]),
                        NOUN=random.choice(combined_pos["NOUN"]),
                        ADJ=random.choice(combined_pos["ADJ"]),
                        ADV=random.choice(combined_pos["ADV"]),
                        PRON=random.choice(combined_pos["PRON"])
                    )
                    if is_grammatically_correct(filled):
                        return filled, True
                except (KeyError, IndexError):
                    continue

        # Fallback to simple concatenation
        return f"{response['text']} {question['text']}", False
    except Exception as e:
        logger.error(f"Error combining response/question: {str(e)}")
        return f"{response['text']} {question['text']}", False

def prepare_triggers() -> Dict[str, List]:
    """Pre-process triggers with error handling"""
    try:
        processed = defaultdict(list)
        for category, data in REPLY_POOLS.items():
            for trigger in data["triggers"]:
                doc = nlp(trigger.lower())
                processed[category].append(doc)
        return processed
    except Exception as e:
        logger.error(f"Error preparing triggers: {str(e)}")
        return defaultdict(list)

TRIGGERS_NLP = prepare_triggers()

class UserMessage(BaseModel):
    message: str

class SallyResponse(BaseModel):
    matched_word: str
    matched_category: str
    confidence: float
    replies: List[str]
    grammar_status: List[str]
    components: List[Dict]
    error: Optional[str] = None

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

@app.post("/analyze", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    try:
        message = user_input.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Empty message")
        
        # Semantic matching
        matched_category, matched_word, confidence = nlp_match(message)
        category_data = REPLY_POOLS.get(matched_category, REPLY_POOLS["general"])
        
        # Generate validated responses
        replies = []
        grammar_status = []
        components = []
        
        for _ in range(2):
            response = random.choice(category_data["responses"])
            question = random.choice(category_data["questions"])
            
            combined_text, was_mixed = combine_response_question(response, question)
            
            replies.append(combined_text)
            grammar_status.append("Mixed successfully" if was_mixed else "Fallback combination")
            components.append({
                "response": response["text"],
                "question": question["text"],
                "mixed": was_mixed
            })
        
        return {
            "matched_word": matched_word or "general",
            "matched_category": matched_category,
            "confidence": round(confidence, 2),
            "replies": replies,
            "grammar_status": grammar_status,
            "components": components
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_message: {str(e)}")
        return {
            "matched_word": "",
            "matched_category": "error",
            "confidence": 0.0,
            "replies": [],
            "grammar_status": [],
            "components": [],
            "error": f"Processing error: {str(e)}"
        }

def nlp_match(message: str) -> Tuple[str, str, float]:
    """Enhanced matching with error handling"""
    try:
        doc = nlp(message.lower())
        best_match = ("general", None, 0.0)
        
        for category, triggers in TRIGGERS_NLP.items():
            for trigger_doc in triggers:
                similarity = doc.similarity(trigger_doc)
                if similarity > best_match[2]:
                    best_match = (category, trigger_doc.text, similarity)
        
        # Fallback to exact match if confidence is low
        if best_match[2] < 0.65:
            words = message.lower().split()
            for word in words:
                for category, data in REPLY_POOLS.items():
                    if word in data["triggers"]:
                        return (category, word, 0.8)
        
        return best_match
    except Exception as e:
        logger.error(f"Error in nlp_match: {str(e)}")
        return ("general", None, 0.0)

