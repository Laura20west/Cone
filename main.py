import json
import random
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

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

# Initialize models
class ChatbotApp(App):
    def build(self):
        self.dataset = self.load_dataset("cone03.txt")
        self.paraphrase_model, self.qgen_model, self.qgen_tokenizer = self.initialize_models()
        
        layout = BoxLayout(orientation='vertical')
        self.input_box = TextInput(size_hint=(1, 0.1), multiline=False)
        self.output_label = Label(size_hint=(1, 0.9), text='Chatbot: Hello! What’s on your mind?')

        send_button = Button(text='Send', size_hint=(1, 0.1))
        send_button.bind(on_press=self.on_send)

        layout.add_widget(self.output_label)
        layout.add_widget(self.input_box)
        layout.add_widget(send_button)
        return layout

    def load_dataset(self, file_path):
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

    def initialize_models(self):
        paraphrase_model = pipeline("text2text-generation", model="tuner007/pegasus_paraphrase", device=0)
        qgen_tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
        qgen_model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
        return paraphrase_model, qgen_model, qgen_tokenizer

    def on_send(self, instance):
        user_input = self.input_box.text.strip()
        if user_input:
            response = self.generate_response(user_input)
            self.output_label.text += f"\nYou: {user_input}\nChatbot: {response}"
            self.input_box.text = ''

    def generate_response(self, user_input):
        relevant_categories = self.get_relevant_categories(user_input)
        matched_text = self.find_best_match(user_input, relevant_categories)
        return self.create_response(matched_text)

    def get_relevant_categories(self, user_input):
        relevant_categories = set()
        words = re.findall(r'\w+', user_input.lower())
        
        for word in words:
            for category, keywords in CATEGORY_KEYWORDS.items():
                if word in keywords:
                    relevant_categories.add(category)
        
        return relevant_categories

    def find_best_match(self, user_input, relevant_categories):
        candidates = []
        for category in relevant_categories:
            if category in self.dataset:
                category_content = self.dataset[category]
                responses = category_content.get('responses', [])
                candidates.extend(responses)
        
        if not candidates:
            return "I’m not sure how to respond to that."
        
        # Vectorization and cosine similarity
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(candidates)
        query_vec = vectorizer.transform([user_input])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-5:][::-1]
        return random.choice([candidates[i] for i in top_indices])

    def create_response(self, matched_text):
        return matched_text if matched_text else "That's interesting. What do you think?"

if __name__ == "__main__":
    ChatbotApp().run()
        
