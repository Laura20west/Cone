from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import Dict, List, Optional
import spacy
from collections import defaultdict, deque

app = FastAPI()

# Load spaCy model
nlp = spacy.load("en_core_web_md")

# ===== SECURITY CONFIGURATION =====
AUTHORIZED_OPERATORS = {
    "cone180",
    "operator2@company.com",
    "admin@company.com"
}

async def verify_operator(
    x_operator_email: Optional[str] = Header(None),
):
    """Middleware to validate operator credentials"""
    if not x_operator_email or x_operator_email not in AUTHORIZED_OPERATORS:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized operator email"
        )
    return x_operator_email

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== APPLICATION CORE =====
REPLY_POOLS: Dict[str, Dict] = {
    "fuck": {
        "triggers": ["You are a beautiful woman and I want to fuck you", "You are extremely hot, can you fuck me", "How are you doing ", "can i fuck you", "i want to fuck you", "i want us to fuck tonight", "I am ready to fuck you, what about you, are you ready to fuck me", "fuck", "fuckbuddies"],
        "responses": [
            "Fuck me like you mean it—deep, hard, and desperate.",
            "fuck me",
            # ... (all existing responses)
        ],
        "questions": [
            "Do you like when a girl talks dirty about how wet her pussy gets for you?",
            "can i suck it?",
            "spank me?"
            # ... (all existing questions)
        ],
    },
    # ... (other categories)
}

# Precompute combinations
CATEGORY_QUEUES = {}
for category, data in REPLY_POOLS.items():
    responses = data["responses"]
    questions = data["questions"]
    combinations = [(r_idx, q_idx) for r_idx in range(len(responses)) for q_idx in range(len(questions))]
    random.shuffle(combinations)
    CATEGORY_QUEUES[category] = deque(combinations)

# NLP processing
def prepare_triggers():
    processed = defaultdict(list)
    for category, data in REPLY_POOLS.items():
        for trigger in data["triggers"]:
            doc = nlp(trigger.lower())
            processed[category].append(doc)
    return processed

TRIGGERS_NLP = prepare_triggers()

# ===== MODELS =====
class UserMessage(BaseModel):
    message: str

class SallyResponse(BaseModel):
    matched_word: str
    matched_category: str
    confidence: float
    replies: List[str]

# ===== ENDPOINTS =====
@app.post("/per", response_model=SallyResponse)
async def analyze_message(
    request: Request,
    user_input: UserMessage,
    operator_email: str = Depends(verify_operator)  # Enforces authorization
):
    """Main endpoint with proper security"""
    # NLP processing
    message = user_input.message.strip()
    matched_category, matched_word, confidence = nlp_match(message)
    
    # Get response queue
    category_data = REPLY_POOLS[matched_category]
    queue = CATEGORY_QUEUES[matched_category]
    
    # Generate replies
    replies = []
    for _ in range(2):
        if queue:
            r_idx, q_idx = queue.popleft()
            response = category_data["responses"][r_idx]
            question = category_data["questions"][q_idx]
            replies.append(f"{response} {question}")
        else:
            break
    
    return {
        "matched_word": matched_word or "general",
        "matched_category": matched_category,
        "confidence": round(confidence, 2),
        "replies": replies if replies else ["finished token, contact developer"]
    }

def nlp_match(message: str) -> tuple:
    """NLP matching logic"""
    doc = nlp(message.lower())
    best_match = ("general", None, 0.0)
    
    for category, triggers in TRIGGERS_NLP.items():
        for trigger_doc in triggers:
            similarity = doc.similarity(trigger_doc)
            if similarity > best_match[2]:
                best_match = (category, trigger_doc.text, similarity)
    
    # Fallback to exact matches
    words = message.lower().split()
    for word in words:
        for category, data in REPLY_POOLS.items():
            if word in data["triggers"] and best_match[2] < 0.7:
                best_match = (category, word, 0.8)
    
    return best_match

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
