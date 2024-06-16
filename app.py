import re
import pickle
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
import logging
from bs4 import BeautifulSoup
import requests

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load LDA model and vectorizer using pickle
print("Loading LDA model and vectorizer...")
lda = joblib.load('models/lda_model.pkl')
print("LDA model loaded successfully.")

vectorizer = joblib.load('models/vectorizer.pkl')
print("Vectorizer loaded successfully.")

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

def preprocess_text(text):
    # Remove numbers and special characters
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    # Join tokens back into text
    processed_text = ' '.join(tokens)
    return processed_text

@app.route('/predict_topic', methods=['POST'])
def predict_topic():
    data = request.json
    urls = data.get('urls', [])
    print('recieved urls')
    texts = []
    for url in urls:
        text = extract_text_from_url(url)
        if text:
            texts.append(text)

    print("Preprocessing texts...")
    processed_texts = [preprocess_text(text) for text in texts]
    print("Texts preprocessed successfully.")

    print("Vectorizing texts...")
    text_vectorized = vectorizer.transform(processed_texts)
    print("Texts vectorized successfully.")

    print("Predicting topics...")
    topic_distributions = lda.transform(text_vectorized)
    print("Topic prediction completed.")

    topics = []
    for dist in topic_distributions:
        topic_index = dist.argmax()
        topic_probability = dist.max()
        topic_name = f"Topic #{topic_index}"
        topics.append({'topic': str(topic_index), 'probability': topic_probability})
        # topics.append(topic_index)
    
    print(topics)
    print("Returning predicted topics.")
    return jsonify(topics)

def extract_text_from_url(url):
    try:
        logging.info(f'Extracting text from URL: {url}')
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text based on HTML structure of news websites
        paragraphs = soup.find_all('p')
        article_text = ' '.join([p.get_text() for p in paragraphs])
        logging.info('Text extraction complete')
        return article_text
    
    except Exception as e:
        logging.error(f"Error extracting text: {e}")
        return None


if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
    print("Flask app is running.")
