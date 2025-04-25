from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
from spacy.tokens import Token
import random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import logging
from fastapi.responses import JSONResponse

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize spacy and custom token attributes
nlp = spacy.load("en_core_web_md")
Token.set_extension("used_in_responses", default=False, force=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MorphologicalAnalyzer:
    def __init__(self):
        self.used_lemmas = set()
        self.used_tokens = set()
    
    def check_uniqueness(self, token: Token) -> bool:
        """Check if token's lemma has been used before"""
        return token.lemma_ not in self.used_lemmas and token.text not in self.used_tokens
    
    def mark_used(self, token: Token):
        """Mark a token as used"""
        self.used_lemmas.add(token.lemma_)
        self.used_tokens.add(token.text)
        token._.used_in_responses = True
    
    def reset(self):
        """Clear all used tokens"""
        self.used_lemmas = set()
        self.used_tokens = set()

morph_analyzer = MorphologicalAnalyzer()

# Enhanced reply pools with lemma tracking
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

def process_texts():
    """Process all texts and tag POS/morphology"""
    processed_pools = {}
    for category, data in REPLY_POOLS.items():
        processed = {"triggers": data["triggers"], "responses": [], "questions": []}
        
        for text in data["responses"]:
            doc = nlp(text)
            processed["responses"].append({
                "text": text,
                "tokens": [token for token in doc],
                "pos": {token.pos_: token.text for token in doc}
            })
        
        for text in data["questions"]:
            doc = nlp(text)
            processed["questions"].append({
                "text": text,
                "tokens": [token for token in doc],
                "pos": {token.pos_: token.text for token in doc}
            })
        
        processed_pools[category] = processed
    return processed_pools

PROCESSED_POOLS = process_texts()

class UniqueResponseGenerator:
    def __init__(self):
        self.max_attempts = 50
    
    def generate_response(self, category: str) -> Tuple[str, Dict]:
        pool = PROCESSED_POOLS.get(category, PROCESSED_POOLS["greeting"])
        
        for _ in range(self.max_attempts):
            # Select random response and question
            response = random.choice(pool["responses"])
            question = random.choice(pool["questions"])
            
            # Combine tokens
            combined_tokens = response["tokens"] + question["tokens"]
            
            # Filter for unused tokens
            unique_tokens = [
                token for token in combined_tokens 
                if not token._.used_in_responses and morph_analyzer.check_uniqueness(token)
            ]
            
            if not unique_tokens:
                continue
                
            # Select tokens maintaining POS balance
            selected_tokens = self._select_tokens(unique_tokens)
            
            if selected_tokens:
                # Build sentence
                sentence = self._construct_sentence(selected_tokens)
                
                # Mark tokens as used
                for token in selected_tokens:
                    morph_analyzer.mark_used(token)
                
                return sentence, {
                    "source_response": response["text"],
                    "source_question": question["text"],
                    "used_lemmas": [token.lemma_ for token in selected_tokens]
                }
        
        # Fallback with used words if no unique combination found
        return self._fallback_response(pool)

    def _select_tokens(self, tokens: List[Token]) -> List[Token]:
        """Select tokens maintaining grammatical structure"""
        # Group by POS
        pos_groups = defaultdict(list)
        for token in tokens:
            pos_groups[token.pos_].append(token)
        
        # Ensure we have required POS types
        required_pos = ["VERB", "NOUN", "PRON"]
        if not all(pos in pos_groups for pos in required_pos):
            return []
        
        # Select tokens
        selected = []
        selected.append(random.choice(pos_groups["PRON"]))
        selected.append(random.choice(pos_groups["VERB"]))
        selected.append(random.choice(pos_groups["NOUN"]))
        
        # Optionally add adjective/adverb
        if "ADJ" in pos_groups and random.random() > 0.5:
            selected.append(random.choice(pos_groups["ADJ"]))
        if "ADV" in pos_groups and random.random() > 0.5:
            selected.append(random.choice(pos_groups["ADV"]))
            
        return selected

    def _construct_sentence(self, tokens: List[Token]) -> str:
        """Construct grammatically correct sentence"""
        # Basic sentence assembly
        sentence = " ".join(token.text for token in tokens)
        
        # Capitalize first letter
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
            
        # Add question mark if it's a question pattern
        if any(token.text.lower() in ["how", "what", "where", "can"] for token in tokens):
            sentence += "?"
        else:
            sentence += "."
            
        return sentence

    def _fallback_response(self, pool: Dict) -> Tuple[str, Dict]:
        """Fallback response when no unique words available"""
        response = random.choice(pool["responses"])
        question = random.choice(pool["questions"])
        return f"{response['text']} {question['text']}", {
            "source_response": response["text"],
            "source_question": question["text"],
            "used_lemmas": "fallback"
        }

response_generator = UniqueResponseGenerator()

@app.middleware("http")
async def reset_analyzer_middleware(request: Request, call_next):
    """Reset morphological analyzer for each request"""
    morph_analyzer.reset()
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
        
        # Match category
        doc = nlp(message.lower())
        matched_category = "explicit" if any(
            token.text in PROCESSED_POOLS["explicit"]["triggers"] for token in doc
        ) else "greeting"
        
        # Generate unique responses
        response, resp_meta = response_generator.generate_response(matched_category)
        question, ques_meta = response_generator.generate_response(matched_category)
        
        return SallyResponse(
            response=response,
            question=question,
            components={
                "response_sources": resp_meta,
                "question_sources": ques_meta
            }
        )
        
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
