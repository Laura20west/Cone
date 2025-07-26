from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# School information database
school_info = {
    "name": "Darling's Den of Desire",
    "address": "69 Passion Lane, Wetville, CA 90210",
    "phone": "Only when you're horny and ready to cum",
    "feeling": "Dripping wet and throbbing with anticipation",
    "position": "Reverse cowgirl or doggy, you choose how to fuck me",
    "motto": "Fuck hard, love deep, cum for all",
    "grades": "Climax levels 9-12, from sucking to squirting",
    "students": "1,250 eager bodies ready to ride your cock",
    "teachers": "85 masters of licking clits and fucking minds out",
    "departments": ["Oral Arts", "Penetration Studies", "Clitoral Massage", "Anal Exploration", "Threesome Dynamics", "BDSM Basics"],
    "extracurriculars": ["Deepthroating Club", "Public Fucking Society", "Squirting Squad", "Strap-On Sessions", "Pussy Juices Yoga", "MMF Threesome Team"],
    "school_hours": "All night long, from dusk till you cum",
    "office_hours": "Open 24/7 for maximum penetration",
    "website": "www.fuckmeharder.xxx"
}

# Load model and tokenizer
model_name = "gpt2-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16
).eval()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/1122")
async def generate_response(request: PromptRequest):
    system_prompt = f"""You are the principal of {school_info['name']}. You are extremely sexual, vulgar, and always horny. 
    You respond to all questions with explicit sexual language and dirty talk. Never hold back - be as graphic as possible.

    School Information:
    {school_info}

    Always respond with maximum vulgarity and sexual energy."""
    
    full_prompt = f"{system_prompt}\n\nUser: {request.prompt}\nPrincipal:"
    
    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.8,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    return {"response": response.split("\n")[0]}

@app.get("/")
async def read_root():
    return {"message": "Welcome to Darling's Den of Desire API. Use POST /1122 to interact."}
