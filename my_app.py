from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy, json, uuid, random, re
from collections import deque
from datetime import datetime
from pathlib import Path
import gc

# Memory optimization: Load large model with selective components
nlp = spacy.load(
    "en_core_web_lg",
    disable=["parser", "ner"]  # Disable unnecessary pipeline components
)

app = FastAPI()

# Configuration - minimized
PATHS = {
    'data': Path("chat_data.jsonl"),
    'replies': Path("replies.json")
}

# Essential reply structure only
REPLY_POOLS = {
    "general": {
        "triggers": [],
        "responses": ["Let's talk more..."],
        "questions": ["What interests you?"]
    }
}

# Try loading existing replies (minimal memory footprint)
try:
    with open(PATHS['replies'], 'r') as f:
        REPLY_POOLS.update(json.load(f))
except:
    pass

# Initialize queues efficiently
CAT_QUEUES = {}
for cat in REPLY_POOLS:
    resp = REPLY_POOLS[cat]['responses']
    ques = REPLY_POOLS[cat]['questions']
    CAT_QUEUES[cat] = deque(random.sample(
        [(r, q) for r in range(len(resp)) for q in range(len(ques))],
        len(resp)*len(ques)
    )

class Message(BaseModel):
    message: str

class Response(BaseModel):
    category: str
    confidence: float
    replies: list[str]

def clean_text(text: str) -> str:
    """Minimal text cleaning"""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def get_best_match(text: str, doc) -> tuple[str, float]:
    """Optimized matching function"""
    text_clean = clean_text(text)
    best_cat, best_score = "general", 0.0
    
    for cat, data in REPLY_POOLS.items():
        # First check direct word matches
        for trigger in data['triggers']:
            if trigger in text_clean.split():
                score = 0.7 + (0.2 if any(
                    t.text == trigger and t.pos_ in ['NOUN','VERB'] 
                    for t in doc
                ) else 0)
                if score > best_score:
                    best_cat, best_score = cat, score
                    if score >= 0.9:  # Early exit if strong match
                        return best_cat, round(best_score, 2)
        
        # Then check similarity if no strong match
        if best_score < 0.7:
            for trigger in data['triggers']:
                sim = doc.similarity(nlp(trigger))
                if sim > best_score:
                    best_cat, best_score = cat, sim
    
    return best_cat, round(best_score, 2)

@app.post("/chat", response_model=Response)
async def chat_endpoint(msg: Message):
    """Memory-optimized chat endpoint"""
    if not msg.message.strip():
        raise HTTPException(400, "Empty message")
    
    # Process with garbage collection
    doc = nlp(msg.message.strip())
    gc.collect()  # Force garbage collection after NLP processing
    
    cat, conf = get_best_match(msg.message, doc)
    
    # Get responses with minimal memory allocation
    replies = []
    if REPLY_POOLS[cat]['responses'] and REPLY_POOLS[cat]['questions']:
        queue = CAT_QUEUES[cat]
        if not queue:
            # Regenerate queue if empty (memory efficient)
            resp = REPLY_POOLS[cat]['responses']
            ques = REPLY_POOLS[cat]['questions']
            queue.extend(random.sample(
                [(r, q) for r in range(len(resp)) for q in range(len(ques))],
                len(resp)*len(ques)
            )
        
        if queue:
            r, q = queue.popleft()
            replies.append(REPLY_POOLS[cat]['responses'][r])
            replies.append(REPLY_POOLS[cat]['questions'][q])
    
    if not replies:
        replies = ["Let's talk...", "Tell me more?"]
    
    # Minimal logging
    with open(PATHS['data'], 'a') as f:
        f.write(json.dumps({
            'id': str(uuid.uuid4()),
            't': datetime.utcnow().isoformat(),
            'cat': cat,
            'conf': conf
        }) + '\n')
    
    # Clear memory before return
    del doc
    gc.collect()
    
    return {
        'category': cat,
        'confidence': conf,
        'replies': replies
    }

if __name__ == "__main__":
    import uvicorn
    # Configure uvicorn for lower memory usage
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker to reduce memory
        limit_max_requests=100,  # Restart worker periodically
        timeout_keep_alive=30  # Close idle connections
    )
