from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import nltk
from nltk.chat.util import Chat, reflections
import re
import random
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# NLTK configurations
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


# ChatMessage model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'


# Define responses for the chatbot
pairs = [
    ['(.*)hello(.*)', ["Hello, {}! How can I help you today?"]],
    ['(.*)how are you(.*)', ["I'm good. How are you?"]],
    ['(.*)good(.*)', ["Okay. What can I do for you today?"]],
    ['(.*)your name(.*)', ["I'm a medical and mental health chatbot.", "You can call me Medi."]],
    ['(.*)help(.*)', ['I can provide information about medical and mental health conditions. Just ask!']],
    ['(.*)no(.*)', ["Go and eat. Don't let trouble find you."]],
    ['(.*)bye(.*)', ['Goodbye!', 'Bye. Take care!']],
    ['(.*)depressed(.*)', ["I'm sorry to hear that. It's important to talk to someone you trust about how you're feeling."]],
    ['(.*)anxiety(.*)', ["Anxiety can be tough. Have you tried talking to a professional about it?"]],
    ['(.*)stress(.*)', ["Stress is common, but there are ways to manage it. Try relaxation techniques like deep breathing or meditation."]],
]

chatbot = Chat(pairs, reflections)


def get_bot_response(user_input):
    username = session.get('username', 'User')
    # Mapping of symptoms to responses
    symptom_responses = {
        "headache": ("migraine", "Take Ibuprofen"),
        "fever": ("flu", "Take Paracetamol"),
        "cough": ("common cold", "Take Cough Syrup"),
        "stomachache": ("hunger", "Go and eat something, don’t allow sapa to wound you."),
        "malaria": ("malaria", "Take Antimalarial Medication and Rest"),
        "sore throat": ("streptococcal pharyngitis", "Take Antibiotics"),
        "diarrhea": ("gastroenteritis", "Stay Hydrated and Rest"),
        "rash": ("contact dermatitis", "Apply Topical Cream and Avoid Irritants"),
        "fatigue": ("anemia", "Take Iron Supplements and Eat Iron-rich Foods"),
        "depressed": ("depression", "It's important to talk to someone you trust about how you're feeling. Seeking professional help can also be beneficial."),
        "anxiety": ("anxiety", "Anxiety can be tough. Have you tried talking to a professional about it?"),
        "stress": ("stress", "Stress is common, but there are ways to manage it. Try relaxation techniques like deep breathing or meditation."),
    }

    # Check if user input matches any symptom
    for symptom, (condition, advice) in symptom_responses.items():
        if symptom in user_input.lower():
            return f"If you have {symptom}, it could be {condition}. {advice}"

    # Check if user input matches any predefined responses
    for pattern, responses in pairs:
        if re.match(pattern, user_input.lower()):
            response = random.choice(responses)
            return response.format(username)

    # Basic response to any mental health-related query
    if re.search(r'\b(mental health|depression|anxiety|stress|therapy|counseling|wellbeing|self-care)\b', user_input, re.IGNORECASE):
        return "Mental health is important. Consider talking to a professional therapist or counselor for personalized advice."

    # If no matching symptom or predefined response found, provide a default response
    return "Sorry, I don't understand what you meant. Can you type again?"


@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('home'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/get')
def get_bot_response_route():
    user_text = request.args.get('msg')
    username = session.get('username')
    bot_response = get_bot_response(user_text)

    # Save user message and bot response to the database
    if username:
        db.session.add(ChatMessage(username=username, message=user_text, sender='user'))
        db.session.add(ChatMessage(username=username, message=bot_response, sender='bot'))
        db.session.commit()

    return jsonify({"user": user_text, "bot": bot_response})


@app.route('/history')
def chat_history():
    username = session.get('username')
    if username:
        messages = ChatMessage.query.filter_by(username=username).all()
        return jsonify([{"sender": msg.sender, "message": msg.message} for msg in messages])
    return jsonify([])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
