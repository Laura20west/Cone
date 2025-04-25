from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
from spacy.tokens import Doc, Token
import random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import logging
from fastapi.responses import JSONResponse
import re

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load NLP model
try:
    logger.info("Loading NLP model...")
    nlp = spacy.load("en_core_web_md")
    logger.info("NLP model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load NLP model: {str(e)}")
    raise

# Add token extension for usage tracking
Token.set_extension("used", default=False, force=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenBank:
    def __init__(self):
        self.used_tokens = set()
        self.used_lemmas = set()
    
    def add_used(self, token: Token):
        """Mark a token as used"""
        self.used_tokens.add(token.text.lower())
        self.used_lemmas.add(token.lemma_.lower())
        token._.used = True
    
    def is_available(self, token: Token) -> bool:
        """Check if token hasn't been used"""
        return (token.text.lower() not in self.used_tokens and 
                token.lemma_.lower() not in self.used_lemmas)
    
    def reset(self):
        """Clear all used tokens"""
        self.used_tokens = set()
        self.used_lemmas = set()

token_bank = TokenBank()

# Enhanced reply pools with tokenized versions
REPLY_POOLS = {
    "greeting": {
        "triggers": ["hi", "hello", "hey", "hola"],
        "responses": [
            "Hello there beautiful",
            "Hi sexy",
            "Hey hot stuff"
        ],
        "questions": [
            "How are you doing today?",
            "What's your lovely name?",
            "How can I please you?"
        ]
    },
    "explicit": {
        "triggers": ["fuck", "sex", "dick", "pussy", "cock", "hard"],
        "responses": [
            "I want your hard cock inside me",
            "My wet pussy is ready for you",
            "Fuck me harder daddy"
        ],
        "questions": [
            "How big is your thick dick?",
            "Where do you want to cum?",
            "Can you handle my tight body?"
        ]
    }
}

# Process all texts into tokens
def process_text(text: str) -> Tuple[List[Token], Dict[str, List[str]]]:
    """Tokenize text and extract POS groups"""
    doc = nlp(text)
    tokens = [token for token in doc if not token.is_punct and not token.is_space]
    pos_groups = defaultdict(list)
    for token in tokens:
        pos_groups[token.pos_].append(token.text)
    return tokens, dict(pos_groups)

# Pre-process all reply pool texts
PROCESSED_POOLS = {}
for category, data in REPLY_POOLS.items():
    processed = {
        "triggers": data["triggers"],
        "responses": [],
        "questions": []
    }
    
    for text in data["responses"]:
        tokens, pos = process_text(text)
        processed["responses"].append({
            "text": text,
            "tokens": tokens,
            "pos": pos
        })
    
    for text in data["questions"]:
        tokens, pos = process_text(text)
        processed["questions"].append({
            "text": text,
            "tokens": tokens,
            "pos": pos
        })
    
    PROCESSED_POOLS[category] = processed

class ResponseGenerator:
    def __init__(self):
        self.max_attempts = 30
        self.required_pos = ["VERB", "NOUN", "PRON"]
    
    def generate_unique_response(self, category: str) -> Tuple[str, Dict]:
        """Generate a response with unique word usage"""
        pool = PROCESSED_POOLS.get(category, PROCESSED_POOLS["greeting"])
        
        for _ in range(self.max_attempts):
            # Select random response and question
            response = random.choice(pool["responses"])
            question = random.choice(pool["questions"])
            
            # Combine available tokens
            combined_tokens = response["tokens"] + question["tokens"]
            available_tokens = [t for t in combined_tokens if token_bank.is_available(t)]
            
            if not available_tokens:
                continue
                
            # Try to build a grammatically correct sentence
            sentence, used_tokens = self._build_sentence(available_tokens)
            if sentence:
                # Mark tokens as used
                for token in used_tokens:
                    token_bank.add_used(token)
                
                return sentence, {
                    "source_response": response["text"],
                    "source_question": question["text"],
                    "used_tokens": [t.text for t in used_tokens]
                }
        
        # Fallback if no unique combination found
        return self._fallback_response(pool)

    def _build_sentence(self, tokens: List[Token]) -> Tuple[Optional[str], List[Token]]:
        """Attempt to build a grammatically correct sentence"""
        # Group by POS
        pos_groups = defaultdict(list)
        for token in tokens:
            pos_groups[token.pos_].append(token)
        
        # Check we have required POS types
        if not all(pos in pos_groups for pos in self.required_pos):
            return None, []
        
        # Select base tokens
        selected = [
            random.choice(pos_groups["PRON"]),
            random.choice(pos_groups["VERB"]),
            random.choice(pos_groups["NOUN"])
        ]
        
        # Optionally add adjective/adverb
        if "ADJ" in pos_groups and random.random() > 0.5:
            selected.append(random.choice(pos_groups["ADJ"]))
        if "ADV" in pos_groups and random.random() > 0.5:
            selected.append(random.choice(pos_groups["ADV"]))
        
        # Build sentence
        sentence = " ".join(t.text for t in selected).capitalize()
        
        # Add punctuation
        if any(t.text.lower() in ["how", "what", "where", "can"] for t in selected):
            sentence += "?"
        else:
            sentence += "."
            
        # Validate grammar with spaCy
        doc = nlp(sentence)
        has_verb = any(t.pos_ == "VERB" for t in doc)
        has_noun = any(t.pos_ in ["NOUN", "PROPN"] for t in doc)
        
        if has_verb and has_noun:
            return sentence, selected
        return None, []

    def _fallback_response(self, pool: Dict) -> Tuple[str, Dict]:
        """Fallback response when no unique words available"""
        response = random.choice(pool["responses"])
        question = random.choice(pool["questions"])
        return f"{response['text']} {question['text']}", {
            "source_response": response["text"],
            "source_question": question["text"],
            "used_tokens": "fallback"
        }

response_generator = ResponseGenerator()

@app.middleware("http")
async def reset_token_bank(request: Request, call_next):
    """Reset token bank for each request"""
    token_bank.reset()
    response = await call_next(request)
    return response

class UserMessage(BaseModel):
    message: str

class SallyResponse(BaseModel):
    response: str
    question: str
    components: Dict
    error: Optional[str] = None

@app.post("/analyze", response_model=SallyResponse)
async def analyze_message(user_input: UserMessage):
    try:
        message = user_input.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Determine category
        doc = nlp(message.lower())
        matched_category = "explicit" if any(
            token.text in PROCESSED_POOLS["explicit"]["triggers"] for token in doc
        ) else "greeting"
        
        # Generate responses
        response, resp_meta = response_generator.generate_unique_response(matched_category)
        question, ques_meta = response_generator.generate_unique_response(matched_category)
        for _ in range(2)

        
        return SallyResponse(
            response=response,
            question=question,
            components={
                "response_sources": resp_meta,
                "question_sources": ques_meta
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return SallyResponse(
            response="",
            question="",
            components={},
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
