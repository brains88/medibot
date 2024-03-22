from flask import Flask, render_template, request
import nltk
from nltk.chat.util import Chat, reflections
import re
import random

app = Flask(__name__)

# NLTK configurations
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Define responses for the chatbot
pairs = [
    ['(.*)hello(.*)', ['Hello!', 'Hi there!', "I'm Medi. How can I help you today?"]],
    ['(.*)how are you(.*)', ["I'm good. How are you?"]],
    ['(.*)good(.*)', ["Okay. What can I do for you today?"]],
    ['(.*)your name(.*)', ["I'm a medical chatbot.", "You can call me Medi."]],
    ['(.*)help(.*)', ['I can provide information about medical conditions. Just ask!']],
    ['(.*)no(.*)', ["Go and eat. Don't let trouble find you."]],
    ['(.*)bye(.*)', ['Goodbye!', 'Bye. Take care!']],
]

chatbot = Chat(pairs, reflections)

def get_bot_response(user_input):
    # Mapping of symptoms to responses
    symptom_responses = {
        "headache": ("migraine", "Take Ibuprofen"),
        "fever": ("flu", "Take Paracetamol"),
        "cough": ("common cold", "Take Cough Syrup"),
        "stomachache": ("indigestion or hunger", "Take Antacid or Eat something"),
        "malaria": ("malaria", "Take Antimalarial Medication and Rest"),
        "sore throat": ("streptococcal pharyngitis", "Take Antibiotics"),
        "diarrhea": ("gastroenteritis", "Stay Hydrated and Rest"),
        "rash": ("contact dermatitis", "Apply Topical Cream and Avoid Irritants"),
        "fatigue": ("anemia", "Take Iron Supplements and Eat Iron-rich Foods"),
    }

    # Check if user input matches any symptom
    for symptom, (condition, advice) in symptom_responses.items():
        if symptom in user_input.lower():
            return f"If you have {symptom}, it could be {condition}. {advice}"

    # Check if user input matches any predefined responses
    for pattern, responses in pairs:
        if re.match(pattern, user_input.lower()):
            return random.choice(responses)

    # If no matching symptom or predefined response found, provide a default response
    return "Sorry, I don't understand what you meant. Can you type again?"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get')
def get_bot_response_route():
    user_text = request.args.get('msg')
    bot_response = get_bot_response(user_text)
    return bot_response

if __name__ == '__main__':
    app.run(debug=True)
