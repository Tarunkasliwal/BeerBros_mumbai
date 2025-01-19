import streamlit as st
import tweepy
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from dotenv import load_dotenv
import os
import requests
from textblob import TextBlob
from collections import Counter
import re

# Load environment variables
load_dotenv()

# Initialize NLTK
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()

# Constants for LangFlow API
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "e889a07c-43c2-42ff-ab2a-375f6f7540b3"
FLOW_ID = "51a07a7b-d922-42c6-809f-4755f23d200d"
APPLICATION_TOKEN = os.getenv("LANGFLOW_APPLICATION_TOKEN")

# Twitter API Initialization
TWITTER_CLIENT = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)


class LangFlowClient:
    def __init__(self):
        self.base_url = BASE_API_URL
        self.langflow_id = LANGFLOW_ID
        self.application_token = APPLICATION_TOKEN

    def generate_ad_with_ai(self, context_data, endpoint=FLOW_ID):
        api_url = f"{self.base_url}/lf/{self.langflow_id}/api/v1/run/{endpoint}"
        prompt = f"""
        Generate creative ad copy based on the following context:
        Trending Topics: {context_data['trending_topics']}
        Sentiment: {context_data['sentiment']}
        Key Benefits: {context_data['benefits']}
        Pain Points: {context_data['pain_points']}
        Generate 3 different ad variations that incorporate these insights.
        """
        payload = {"input_value": prompt, "output_type": "chat", "input_type": "chat"}
        headers = {
            "Authorization": f"Bearer {self.application_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error generating AI ad: {e}")
            return None


class TwitterAnalyzer:
    def fetch_tweets(self, query, limit=100):
        tweets = []
        try:
            for tweet in tweepy.Paginator(
                TWITTER_CLIENT.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=["created_at", "public_metrics", "lang", "text"],
            ).flatten(limit=limit):
                sentiment_scores = sia.polarity_scores(tweet.text)
                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at,
                    "sentiment_score": sentiment_scores["compound"],
                    "sentiment_category": self.categorize_sentiment(
                        sentiment_scores["compound"]
                    ),
                    "likes": tweet.public_metrics["like_count"],
                    "retweets": tweet.public_metrics["retweet_count"],
                    "lang": tweet.lang,
                }
                tweets.append(tweet_data)
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return pd.DataFrame()

        return pd.DataFrame(tweets)

    def categorize_sentiment(self, score):
        if score <= -0.05:
            return "negative"
        elif score >= 0.05:
            return "positive"
        else:
            return "neutral"

    def analyze_trending_topics(self, tweets_df):
        hashtags = []
        for text in tweets_df.get("text", []):
            hashtags.extend(re.findall(r"#(\w+)", text))
        counter = Counter(hashtags)
        return [tag for tag, count in counter.most_common(5)]

    def extract_key_benefits(self, positive_tweets):
        benefits = []
        for text in positive_tweets.get("text", []):
            blob = TextBlob(text)
            for sentence in blob.sentences:
                if any(
                    word in sentence.lower()
                    for word in ["great", "amazing", "love", "perfect", "best"]
                ):
                    benefits.append(str(sentence))
        return benefits[:5] if benefits else ["improved experience"]

    def identify_pain_points(self, negative_tweets):
        pain_points = []
        for text in negative_tweets.get("text", []):
            blob = TextBlob(text)
            for sentence in blob.sentences:
                if any(
                    word in sentence.lower()
                    for word in ["bad", "hate", "problem", "issue", "difficult"]
                ):
                    pain_points.append(str(sentence))
        return pain_points[:5] if pain_points else ["common challenges"]


def main():
    st.set_page_config(page_title="Twitter Analysis & Ad Generator", layout="wide")
    st.title("Twitter Analysis & AI-Powered Ad Generation")

    analyzer = TwitterAnalyzer()
    langflow_client = LangFlowClient()

    with st.sidebar:
        st.header("Configuration")
        query = st.text_input("Enter search query:")
        limit = st.number_input(
            "Number of tweets to analyze:", min_value=10, max_value=100, value=50
        )
        if st.button("Analyze"):
            with st.spinner("Analyzing tweets and generating ad suggestions..."):
                tweets_df = analyzer.fetch_tweets(query, limit)
                if tweets_df.empty:
                    st.error("No tweets found. Try a different query.")
                    return

                trending_topics = analyzer.analyze_trending_topics(tweets_df)
                benefits = analyzer.extract_key_benefits(
                    tweets_df[tweets_df["sentiment_score"] > 0]
                )
                pain_points = analyzer.identify_pain_points(
                    tweets_df[tweets_df["sentiment_score"] < 0]
                )

                context_data = {
                    "trending_topics": trending_topics,
                    "sentiment": tweets_df["sentiment_score"].mean(),
                    "benefits": benefits,
                    "pain_points": pain_points,
                }

                ai_ads = langflow_client.generate_ad_with_ai(context_data)

                st.session_state["tweets_df"] = tweets_df
                st.session_state["ai_ads"] = ai_ads

    if "tweets_df" in st.session_state:
        st.subheader("Analyzed Tweets")
        st.datimport streamlit as st
import json
import requests
from typing import Optional
import warnings

try:
    from langflow.load import upload_file
except ImportError:
    warnings.warn("Langflow provides a function to help you upload files to the flow. Please install langflow to use it.")
    upload_file = None

# Constants
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "e889a07c-43c2-42ff-ab2a-375f6f7540b3"
FLOW_ID = "51a07a7b-d922-42c6-809f-4755f23d200d"
APPLICATION_TOKEN = "AstraCS:xsUNsdDvnURyQNmceRHQpJhG:1a244f2ba1c7ff76071f0a016ec73644190ec5d08c2ecd51eb3ba2900e692565"
DEFAULT_TWEAKS = {
    "ChatInput-SnYiF": {},
    "ChatOutput-o0NcW": {},
    "GroqModel-xbFdE": {}
}

def run_flow(
    message: str,
    endpoint: str,
    output_type: str = "chat",
    input_type: str = "chat",
    tweaks: Optional[dict] = None,
    application_token: Optional[str] = None
) -> dict:
    """Run a flow with a given message and optional tweaks."""
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"
    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = None
    
    if tweaks:
        payload["tweaks"] = tweaks
    if application_token:
        headers = {"Authorization": "Bearer " + application_token, "Content-Type": "application/json"}
    
    with st.spinner("Processing your request..."):
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Error: Failed to get a valid response. Status Code: {response.status_code}")
            st.code(response.text, language="json")
            return None
        
        return response.json()

def main():
    st.title("Langflow API Interface")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # API Configuration
    with st.sidebar.expander("API Settings", expanded=False):
        custom_endpoint = st.text_input("Endpoint", value=FLOW_ID)
        custom_token = st.text_input("Application Token", value=APPLICATION_TOKEN, type="password")
        input_type = st.selectbox("Input Type", ["chat", "text"], index=0)
        output_type = st.selectbox("Output Type", ["chat", "text"], index=0)
    
    # Tweaks Configuration
    with st.sidebar.expander("Tweaks Configuration", expanded=False):
        tweaks_str = st.text_area("Tweaks (JSON)", value=json.dumps(DEFAULT_TWEAKS, indent=2))
        try:
            tweaks = json.loads(tweaks_str)
        except json.JSONDecodeError:
            st.sidebar.error("Invalid JSON format for tweaks")
            tweaks = DEFAULT_TWEAKS
    
    # File Upload
    with st.sidebar.expander("File Upload", expanded=False):
        uploaded_file = st.file_uploader("Upload File")
        components = st.text_input("Components (comma-separated)")
        
        if uploaded_file and components and upload_file:
            try:
                # Save uploaded file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                tweaks = upload_file(
                    file_path=tmp_file_path,
                    host=BASE_API_URL,
                    flow_id=custom_endpoint,
                    components=components.split(","),
                    tweaks=tweaks
                )
                os.unlink(tmp_file_path)  # Clean up temporary file
                st.sidebar.success("File uploaded and tweaks updated!")
            except Exception as e:
                st.sidebar.error(f"Error uploading file: {str(e)}")
    
    # Main chat interface
    st.subheader("Chat Interface")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What's your message?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        response = run_flow(
            message=prompt,
            endpoint=custom_endpoint,
            output_type=output_type,
            input_type=input_type,
            tweaks=tweaks,
            application_token=custom_token
        )
        
        if response and 'messages' in response and response['messages']:
            assistant_message = response['messages'][0].get('message', '')
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            with st.chat_message("assistant"):
                st.markdown(assistant_message)
        else:
            with st.chat_message("assistant"):
                st.error("No valid response received from the API")
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()aframe(st.session_state["tweets_df"])

    if "ai_ads" in st.session_state and st.session_state["ai_ads"]:
        st.subheader("AI-Powered Ad Suggestions")
        for ad in st.session_state["ai_ads"]:
            st.write(ad)


if __name__ == "__main__":
    main()
