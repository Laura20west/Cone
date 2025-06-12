import json
import random
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import os

# Predefined keyword categories
CATEGORY_KEYWORDS = {
    "sex": ["fuck", "cock", "boobs", "pussy", "horny", "sex", "suck", "spank", 
            "bondage", "threesome", "dick", "orgasm", "fucking", "nude", "naked",
            "blowjob", "handjob", "anal", "fetish", "kink", "sexy", "erotic", "masturbation"],
    "cars": ["car", "vehicle", "drive", "driving", "engine", "tire", "race", "speed",
             "motor", "wheel", "road", "highway", "license", "driver", "automobile"],
    "age": ["age", "old", "young", "birthday", "years", "aged", "elderly", "youth", 
            "minor", "teen", "teenager", "adult", "senior", "centenarian"],
    "hobbies": ["toy", "fun", "hobbies", "game", "play", "playing", "collect", 
               "activity", "leisure", "pastime", "sport", "craft", "art", "music", "reading"],
    "relationships": ["date", "dating", "partner", "boyfriend", "girlfriend", 
                     "marriage", "marry", "crush", "love", "kiss", "romance",
                     "affection", "commitment", "proposal", "engagement"]
}

# Load dataset preserving categories and content
def load_dataset(file_path):
    if not os.path.exists(file_path):
        print(f"Dataset file not found: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading dataset: {str(e)}")
        return {}

# Initialize models
def initialize_models():
    try:
        paraphrase_model = pipeline(
            "text2text-generation",
            model="tuner007/pegasus_paraphrase",
            device="cpu"
        )
        print("Paraphrase model loaded successfully")
    except Exception as e:
        print(f"Paraphrase model error: {str(e)}")
        paraphrase_model = None
    
    try:
        qgen_tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
        qgen_model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
        print("Question generation model loaded successfully")
    except Exception as e:
        print(f"Question model error: {str(e)}")
        qgen_model = None
        qgen_tokenizer = None
    
    return paraphrase_model, qgen_model, qgen_tokenizer

# Identify relevant categories based on keywords
def get_relevant_categories(user_input):
    relevant_categories = set()
    words = re.findall(r'\w+', user_input.lower())
    
    for word in words:
        for category, keywords in CATEGORY_KEYWORDS.items():
            if word in keywords:
                relevant_categories.add(category)
    
    return relevant_categories

# Find best match within relevant categories with random selection
def find_best_match(user_input, dataset, relevant_categories):
    if not dataset:
        return None
    
    # Get all candidates from relevant categories
    candidates = []
    for category in relevant_categories:
        if category in dataset:
            category_content = dataset[category]
            responses = category_content.get('responses', [])
            questions = category_content.get('questions', [])
            
            # Add all responses and questions from the category
            candidates.extend(responses)
            candidates.extend(questions)
    
    # If no candidates from relevant categories, use all categories
    if not candidates:
        for category, content in dataset.items():
            responses = content.get('responses', [])
            questions = content.get('questions', [])
            candidates.extend(responses)
            candidates.extend(questions)
    
    # Filter out empty candidates
    candidates = [c.strip() for c in candidates if c.strip()]
    
    if not candidates:
        return None
    
    # If we have many candidates, select a random subset for efficiency
    max_candidates = 500
    if len(candidates) > max_candidates:
        candidates = random.sample(candidates, max_candidates)
    
    # Vectorize candidates
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(candidates)
    except Exception as e:
        print(f"Vectorization error: {str(e)}")
        return None
    
    # Vectorize user input
    try:
        query_vec = vectorizer.transform([user_input])
    except:
        return random.choice(candidates)  # Fallback to random selection
    
    # Find best matches
    try:
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        # Get top 5 matches
        top_indices = similarities.argsort()[-5:][::-1]
        # Randomly select from top matches
        selected_index = random.choice(top_indices)
        return candidates[selected_index]
    except:
        return random.choice(candidates)  # Fallback to random selection

# Paraphrase text
def paraphrase_text(text, model):
    if not model or not text.strip():
        return text
    
    try:
        result = model(
            f"paraphrase: {text}",
            max_length=60,
            num_beams=5,
            num_return_sequences=1,
            temperature=0.7
        )
        return result[0]['generated_text']
    except Exception as e:
        print(f"Paraphrase error: {str(e)}")
        return text

# Generate follow-up question
def generate_question(context, model, tokenizer):
    if not model or not context.strip():
        return "What are your thoughts on that?"
    
    try:
        inputs = tokenizer(
            f"generate follow-up question: {context}",
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        outputs = model.generate(
            inputs.input_ids,
            max_length=50,
            num_beams=5,
            early_stopping=True
        )
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return "What do you think about that?"

# Create fluid response with question
def create_response(matched_text, paraphrase_model, qgen_model, qgen_tokenizer):
    # Paraphrase the matched text
    paraphrased = paraphrase_text(matched_text, paraphrase_model)
    
    # Generate follow-up question
    follow_up = generate_question(matched_text, qgen_model, qgen_tokenizer)
    
    # Create seamless connection
    connectors = [
        "By the way,", "Actually,", "You know,", "Anyway,",
        "Speaking of which,", "On that note,", "Curiously,",
        "Incidentally,", "Interestingly,", "Changing topics slightly,",
        "That reminds me,", "To shift gears a bit,"
    ]
    
    # Randomly decide connection style
    if random.random() > 0.4:  # 60% chance to use connector
        return f"{paraphrased} {random.choice(connectors)} {follow_up}"
    return f"{paraphrased} {follow_up}"

# Main chatbot function
def run_chatbot():
    # Load dataset
    dataset = load_dataset("cone03.txt")
    if not dataset:
        print("Failed to load dataset. Exiting.")
        return
    
    print(f"Loaded dataset with {len(dataset)} categories")
    
    # Initialize models
    paraphrase_model, qgen_model, qgen_tokenizer = initialize_models()
    
    print("\nChatbot: Hey there! What's on your mind?\n")
    
    # Conversation history to avoid repetition
    conversation_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChatbot: Gotta run! Talk to you later.")
            break
            
        if not user_input:
            continue
            
        if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
            print("\nChatbot: Catch you later!")
            break
            
        try:
            # Identify relevant categories
            relevant_categories = get_relevant_categories(user_input)
            print(f"Detected categories: {', '.join(relevant_categories) if relevant_categories else 'General'}")
            
            # Find best match from relevant categories
            matched_text = find_best_match(user_input, dataset, relevant_categories)
            
            # Fallback if no match found
            if not matched_text:
                fallbacks = [
                    "That's interesting. What makes you say that?",
                    "I'd love to know more about your perspective.",
                    "That's a unique viewpoint. Tell me more.",
                    "What do you think about that yourself?",
                    "Could you elaborate on that?",
                    "What's your take on this?",
                    "That's something I haven't considered before. What brought this to mind?"
                ]
                matched_text = random.choice(fallbacks)
            
            # Add to history and ensure we don't repeat recent responses
            if matched_text in conversation_history:
                # If we've used this recently, try to find a different match
                print("Avoiding repeated response, finding alternative...")
                matched_text = find_best_match(user_input, dataset, relevant_categories) or random.choice(fallbacks)
            
            # Keep history of last 5 responses
            conversation_history.append(matched_text)
            if len(conversation_history) > 5:
                conversation_history.pop(0)
            
            # Create fluid response
            response = create_response(
                matched_text,
                paraphrase_model,
                qgen_model,
                qgen_tokenizer
            )
            
            print(f"\nChatbot: {response}\n")
        except Exception as e:
            print(f"Error: {str(e)}")
            print("\nChatbot: Hmm, let me think about that differently...\n")

if __name__ == "__main__":
    run_chatbot()
