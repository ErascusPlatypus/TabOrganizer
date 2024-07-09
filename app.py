import re
import pickle
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import warnings
import logging
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, parse_qs

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

app = Flask(__name__)
CORS(app)

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
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

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
        topics.append({'topic': '25', 'probability': 1.0})  
    
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
    
    paragraphs = soup.find_all('p')
    article_text = ' '.join([p.get_text() for p in paragraphs])
    logging.info('Text extraction complete')
    return article_text

def extract_youtube_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
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

@app.route('/')
def home():
    logging.info('Home page accessed')
    return render_template('index.html')

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
    print("Flask app is running.")
