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
from urllib.parse import urlparse, parse_qs

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load LDA model and vectorizer using pickle
print("Loading LDA model and vectorizer...")
lda = joblib.load('models/lda_model.pkl')
#lda = joblib.load('new_lda_model.pkl')
print("LDA model loaded successfully.")

vectorizer = joblib.load('models/vectorizer.pkl')
#vectorizer = joblib.load('new_vectorizer.pkl')
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
    print('received urls:', urls)
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
    
    # If no topics were predicted, assign topic number 25
    if not topics:
        topics.append({'topic': '25', 'probability': 1.0})  # Assigning probability as 1.0 for default topic
    
    print(topics)
    print("Returning predicted topics.")
    return jsonify(topics)

def extract_text_from_url(url):
    try:
        logging.info(f'Extracting content from URL: {url}')
        
        if "youtube.com" in url or "youtu.be" in url:
            return extract_youtube_title(url)
        elif "google.com" in url:
            return extract_google_query(url)
        else:
            return extract_article_text(url)
        
    except Exception as e:
        logging.error(f"Error extracting text: {e}")
        return None

def extract_article_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract text based on HTML structure of news websites
    paragraphs = soup.find_all('p')
    article_text = ' '.join([p.get_text() for p in paragraphs])
    logging.info('Text extraction complete')
    return article_text

def extract_youtube_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract title of YouTube video
    title = soup.find('meta', property='og:title')
    if title:
        video_title = title['content']
        logging.info('YouTube title extraction complete')
        return video_title
    else:
        logging.warning('Could not find YouTube video title')
        return None

def extract_google_query(url):
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        if 'q' in query_params:
            search_query = query_params['q'][0]
            return search_query
        else:
            return None
    
    except Exception as e:
        print(f"Error extracting search query: {e}")
        return None


if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
    print("Flask app is running.")
