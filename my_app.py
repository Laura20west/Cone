from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging
from fastapi.responses import JSONResponse

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load NLP models
try:
    logger.info("Loading NLP models...")
    nlp = spacy.load("en_core_web_md")
    grammar_checker = spacy.load("en_core_web_sm")
    logger.info("NLP models loaded successfully")
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

# Enhanced reply pools with proper POS tagging
REPLY_POOLS = {
    "greeting": {
        "triggers": ["hi", "hello", "hey", "hola"],
        "responses": [
            {"text": "Hello there beautiful", "pos": {"VERB": ["Hello"], "ADJ": ["beautiful"]}},
            {"text": "Hi sexy", "pos": {"VERB": ["Hi"], "ADJ": ["sexy"]}},
            {"text": "Hey hot stuff", "pos": {"VERB": ["Hey"], "ADJ": ["hot"]}}
        ],
        "questions": [
            {"text": "How are you doing today?", "pos": {"ADV": ["How"], "VERB": ["are", "doing"], "PRON": ["you"]}},
            {"text": "What's your lovely name?", "pos": {"NOUN": ["name"], "ADJ": ["lovely"], "PRON": ["your"]}},
            {"text": "How can I please you?", "pos": {"VERB": ["can", "please"], "PRON": ["I", "you"]}}
        ]
    },
    "explicit": {
        "triggers": ["fuck", "sex", "dick", "pussy", "cock", "hard"],
        "responses": [
            {"text": "I want your hard cock inside me", "pos": {"VERB": ["want"], "ADJ": ["hard"], "NOUN": ["cock"], "PRON": ["I", "your"]}},
            {"text": "My wet pussy is ready for you", "pos": {"ADJ": ["wet"], "NOUN": ["pussy"], "VERB": ["is"], "PRON": ["My", "you"]}},
            {"text": "Fuck me harder daddy", "pos": {"VERB": ["Fuck"], "ADV": ["harder"], "NOUN": ["daddy"], "PRON": ["me"]}}
        ],
        "questions": [
            {"text": "How big is your thick dick?", "pos": {"ADJ": ["big", "thick"], "NOUN": ["dick"], "VERB": ["is"], "PRON": ["your"]}},
            {"text": "Where do you want to cum?", "pos": {"VERB": ["do", "want", "cum"], "PRON": ["you"]}},
            {"text": "Can you handle my tight body?", "pos": {"VERB": ["Can", "handle"], "ADJ": ["tight"], "NOUN": ["body"], "PRON": ["you", "my"]}}
        ]
    }
}

def validate_pos_tags():
    """Ensure all entries have complete POS tags"""
    logger.info("Validating POS tags...")
    for category_name, category in REPLY_POOLS.items():
        for item_type in ["responses", "questions"]:
            for item in category[item_type]:
                if "pos" not in item:
                    logger.warning(f"Missing POS tags for {category_name} {item_type}: {item['text']}")
                    doc = nlp(item["text"])
                    pos_tags = defaultdict(list)
                    for token in doc:
                        if not token.is_punct and not token.is_space:
                            pos_tags[token.pos_].append(token.text)
                    item["pos"] = dict(pos_tags)
                # Ensure required POS tags exist
                for required_pos in ["VERB", "NOUN", "ADJ"]:
                    if required_pos not in item["pos"]:
                        item["pos"][required_pos] = []
    logger.info("POS tags validation complete")

validate_pos_tags()

def is_grammatically_correct(text: str) -> bool:
    """Check if the generated text is grammatically sound"""
    try:
        doc = grammar_checker(text)
        # Basic checks for sentence structure
        has_verb = any(token.pos_ == "VERB" for token in doc)
        has_noun = any(token.pos_ in ["NOUN", "PROPN"] for token in doc)
        has_pronoun = any(token.pos_ == "PRON" for token in doc)
        return has_verb and (has_noun or has_pronoun)
    except Exception as e:
        logger.error(f"Grammar check failed for '{text}': {str(e)}")
        return False

def combine_response_question(response: Dict, question: Dict) -> Tuple[str, bool]:
    """Combine response and question elements intelligently"""
    try:
        # Combine vocabulary from both
        combined = {
            "VERB": response["pos"]["VERB"] + question["pos"]["VERB"],
            "NOUN": response["pos"]["NOUN"] + question["pos"]["NOUN"],
            "ADJ": response["pos"]["ADJ"] + question["pos"]["ADJ"],
            "ADV": response["pos"].get("ADV", []) + question["pos"].get("ADV", []),
            "PRON": response["pos"].get("PRON", []) + question["pos"].get("PRON", [])
        }

        # Templates that work well for adult content
        templates = [
            "{VERB} {PRON} {ADV}",
            "{PRON} {VERB} {NOUN} {ADV}",
            "{VERB} {PRON} {ADJ} {NOUN}",
            "How {ADJ} {VERB} {PRON}?",
            "Where {VERB} {PRON} {NOUN}?",
            "{PRON} {VERB} to {VERB} {PRON} {ADV}"
        ]

        # Try multiple combinations
        for _ in range(10):
            template = random.choice(templates)
            try:
                filled = template.format(
                    VERB=random.choice(combined["VERB"]),
                    NOUN=random.choice(combined["NOUN"]),
                    ADJ=random.choice(combined["ADJ"]),
                    ADV=random.choice(combined["ADV"]),
                    PRON=random.choice(combined["PRON"])
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

def match_category(message: str) -> Tuple[str, str, float]:
    """Match message to category with similarity scoring"""
    try:
        doc = nlp(message.lower())
        best_match = ("general", None, 0.0)
        
        for category, data in REPLY_POOLS.items():
            for trigger in data["triggers"]:
                trigger_doc = nlp(trigger)
                similarity = doc.similarity(trigger_doc)
                if similarity > best_match[2]:
                    best_match = (category, trigger, similarity)
        
        # Boost confidence if exact match found
        words = message.lower().split()
        for word in words:
            for category, data in REPLY_POOLS.items():
                if word in data["triggers"] and best_match[2] < 0.7:
                    return (category, word, 0.8)
        
        return best_match
    except Exception as e:
        logger.error(f"Error in matching category: {str(e)}")
        return ("general", None, 0.0)

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
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

@app.post("/analyze", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    try:
        message = user_input.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Processing message: {message}")
        
        # Match category
        matched_category, matched_word, confidence = match_category(message)
        logger.info(f"Matched category: {matched_category} (confidence: {confidence})")
        
        # Get response data
        category_data = REPLY_POOLS.get(matched_category)
        if not category_data:
            raise HTTPException(status_code=400, detail="Category not found")
        
        # Generate responses
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
        
        logger.info(f"Generated replies: {replies}")
        
        return SallyResponse(
            matched_word=matched_word or "",
            matched_category=matched_category,
            confidence=round(confidence, 2),
            replies=replies,
            grammar_status=grammar_status,
            components=components
        )
        
    except HTTPException as he:
        logger.error(f"HTTP error: {str(he.detail)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return SallyResponse(
            matched_word="",
            matched_category="error",
            confidence=0.0,
            replies=[],
            grammar_status=[],
            components=[],
            error=f"Processing error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
