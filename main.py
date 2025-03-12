import streamlit as st
import pickle
import string
import sqlite3
import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# Load model and vectorizer
tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
model = pickle.load(open('model.pkl', 'rb'))

ps = PorterStemmer()


def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = [i for i in text if i.isalnum()]
    y = [i for i in y if i not in stopwords.words('english') and i not in string.punctuation]
    y = [ps.stem(i) for i in y]

    return " ".join(y)


# Initialize database
conn = sqlite3.connect("sms_predictionsm.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        prediction TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
conn.commit()


# Save user to database
def register_user(name, email, password):
    c.execute("SELECT id FROM users WHERE email = ?", (email,))
    if c.fetchone():
        return None  # Email already registered
    c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
    conn.commit()
    return c.lastrowid


def authenticate_user(email, password):
    c.execute("SELECT id, name FROM users WHERE email = ? AND password = ?", (email, password))
    return c.fetchone()


def save_prediction(user_id, message, prediction):
    c.execute("INSERT INTO predictions (user_id, message, prediction) VALUES (?, ?, ?)", (user_id, message, prediction))
    conn.commit()


st.markdown("""
    <style>
        .stApp {
            background: url("https://source.unsplash.com/1600x900/?technology") no-repeat center center fixed;
            background-size: cover;
        }
        .title {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: white;
        }
        .center {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 80vh;
        }
        .stButton>button {
            width: 200px;
            height: 50px;
            font-size: 18px;
            font-weight: bold;
            background-color: #007BFF;
            color: white;
            border-radius: 8px;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'home'
    st.session_state.user_id = None
    st.session_state.user_name = ""

if st.session_state.page == 'home':
    st.markdown("<h1 class='title'>🔐 Welcome</h1>", unsafe_allow_html=True)
    if st.button("Sign Up"):
        st.session_state.page = 'signup'
        st.rerun()
    if st.button("Login"):
        st.session_state.page = 'login'
        st.rerun()

elif st.session_state.page == 'signup':
    st.markdown("<h1 class='title'>📝 Sign Up</h1>", unsafe_allow_html=True)
    name = st.text_input("Enter your name:")
    email = st.text_input("Enter your email:")
    password = st.text_input("Enter your password:", type='password')

    if st.button("Register"):
        if name and email and password:
            user_id = register_user(name, email, password)
            if user_id:
                st.success("Registration successful! Please log in.")
                st.session_state.page = 'login'
                st.rerun()
            else:
                st.error("Email already registered! Try logging in.")

elif st.session_state.page == 'login':
    st.markdown("<h1 class='title'>🔑 Login</h1>", unsafe_allow_html=True)
    email = st.text_input("Enter your email:")
    password = st.text_input("Enter your password:", type='password')

    if st.button("Login"):
        user = authenticate_user(email, password)
        if user:
            st.session_state.user_id, st.session_state.user_name = user
            st.session_state.page = 'welcome'
            st.rerun()
        else:
            st.error("Invalid email or password!")

elif st.session_state.page == 'welcome':
    st.markdown(f"<h1 class='title'>👋 Welcome, {st.session_state.user_name}!</h1>", unsafe_allow_html=True)
    if st.button("🚀 Start Spam Detection"):
        st.session_state.page = 'main'
        st.rerun()
    if st.button("Logout"):
        st.session_state.page = 'home'
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.rerun()

elif st.session_state.page == 'main':
    st.markdown(f"<h1 class='title'>📩 SMS Spam Detection</h1>", unsafe_allow_html=True)
    input_sms = st.text_area("✉ Enter the message", height=150)

    if st.button("🔍 Predict"):
        transformed_sms = transform_text(input_sms)
        vector_input = tfidf.transform([transformed_sms])
        result = model.predict(vector_input)[0]

        prediction_text = "Spam" if result == 1 else "Not Spam"
        icon = "🚨" if result == 1 else "✅"

        st.markdown(
            f"<h2 style='color: {'red' if result == 1 else 'green'}; text-align: center;'>{icon} {prediction_text}</h2>",
            unsafe_allow_html=True)
        save_prediction(st.session_state.user_id, input_sms, prediction_text)

    if st.button("Logout"):
        st.session_state.page = 'home'
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.rerun()

conn.close()
