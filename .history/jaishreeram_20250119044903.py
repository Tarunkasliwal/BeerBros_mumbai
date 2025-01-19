import streamlit as st
import tweepy
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv
from astrapy.db import AstraDB
import requests
from textblob import TextBlob
from collections import Counter
import re

# Load environment variables
load_dotenv()

# Constants for LangFlow
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "e889a07c-43c2-42ff-ab2a-375f6f7540b3"
FLOW_ID = "51a07a7b-d922-42c6-809f-4755f23d200d"
APPLICATION_TOKEN = os.getenv('LANGFLOW_APPLICATION_TOKEN')

class AstraDBManager:
    def __init__(self):
        self.db = AstraDB(
            token=os.getenv('ASTRA_TOKEN'),
            api_endpoint=os.getenv('ASTRA_API_ENDPOINT'),
            namespace=os.getenv('ASTRA_KEYSPACE', 'default_keyspace')
        )
        self.tweets_collection = self.db.collection('tweets')
        
        try:
            collections = self.db.get_collections()
            print(f"Connected to Astra DB: {collections}")
            if not self.tweets_collection:
                self.db.create_collection('tweets')
                self.tweets_collection = self.db.collection('tweets')
        except Exception as e:
            print(f"Error connecting to Astra DB: {e}")
    
    def save_tweet(self, tweet_data):
        try:
            self.tweets_collection.insert_one(tweet_data)
            return True
        except Exception as e:
            print(f"Error saving tweet: {e}")
            return False

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
        
        payload = {
            "input_value": prompt,
            "output_type": "chat",
            "input_type": "chat",
        }
        
        headers = {
            "Authorization": f"Bearer {self.application_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error generating AI ad: {e}")
            return None

class AdGenerator:
    def __init__(self):
        self.templates = [
            {
                "type": "Problem-Solution",
                "template": "Tired of {pain_point}? Discover how {benefit} can transform your experience!"
            },
            {
                "type": "Benefit-Focused",
                "template": "Experience {benefit} like never before! Join thousands of satisfied customers."
            },
            {
                "type": "Trending",
                "template": "Join the conversation about {trending_topic}! See why everyone's talking about {benefit}."
            }
        ]

    def generate_ad_ideas(self, tweets_df):
        ad_ideas = []
        
        trending_topics = self.analyze_trending_topics(tweets_df)
        benefits = self.extract_key_benefits(tweets_df[tweets_df['sentiment_score'] > 0])
        pain_points = self.identify_pain_points(tweets_df[tweets_df['sentiment_score'] < 0])
        
        for template in self.templates:
            ad = {
                "type": template["type"],
                "content": template["template"].format(
                    pain_point=pain_points[0] if pain_points else "common problems",
                    benefit=benefits[0] if benefits else "our solution",
                    trending_topic=trending_topics[0] if trending_topics else "this trending topic"
                ),
                "target_emotion": "positive" if "benefit" in template["template"] else "problem-aware",
                "trending_topic": trending_topics[0] if trending_topics else "general"
            }
            ad_ideas.append(ad)
        
        return ad_ideas

    def analyze_trending_topics(self, tweets_df):
        hashtags = []
        for text in tweets_df.get('text', []):
            hashtags.extend(re.findall(r'#(\w+)', text))
        
        counter = Counter(hashtags)
        return [tag for tag, count in counter.most_common(5)]

    def extract_key_benefits(self, positive_tweets):
        benefits = []
        for text in positive_tweets.get('text', []):
            blob = TextBlob(text)
            for sentence in blob.sentences:
                if any(word in sentence.lower() for word in ['great', 'amazing', 'love', 'perfect', 'best']):
                    benefits.append(str(sentence))
        return benefits[:5] if benefits else ["improved experience"]

    def identify_pain_points(self, negative_tweets):
        pain_points = []
        for text in negative_tweets.get('text', []):
            blob = TextBlob(text)
            for sentence in blob.sentences:
                if any(word in sentence.lower() for word in ['bad', 'hate', 'problem', 'issue', 'difficult']):
                    pain_points.append(str(sentence))
        return pain_points[:5] if pain_points else ["common challenges"]

class TwitterAnalyzer:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        self.db_manager = AstraDBManager()
        self.langflow_client = LangFlowClient()
        nltk.download('vader_lexicon')
        self.sia = SentimentIntensityAnalyzer()
        self.ad_generator = AdGenerator()

    def fetch_tweets(self, query, limit=100):
        tweets = []
        try:
            for tweet in tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics', 'lang', 'text']
            ).flatten(limit=limit):
                
                if not hasattr(tweet, 'text'):
                    print(f"Tweet missing 'text': {tweet}")
                    continue

                sentiment_scores = self.sia.polarity_scores(tweet.text)
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'sentiment_score': sentiment_scores['compound'],
                    'sentiment_category': self.categorize_sentiment(sentiment_scores['compound']),
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count'],
                    'lang': tweet.lang
                }
                tweets.append(tweet_data)
                self.db_manager.save_tweet(tweet_data)
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

    def fetch_and_analyze_tweets(self, query, limit=100):
        tweets_df = self.fetch_tweets(query, limit)
        if tweets_df.empty:
            print("No tweets retrieved.")
            return pd.DataFrame(), [], []
        
        traditional_ad_ideas = self.ad_generator.generate_ad_ideas(tweets_df)
        context_data = {
            'trending_topics': self.ad_generator.analyze_trending_topics(tweets_df),
            'sentiment': tweets_df['sentiment_score'].mean(),
            'benefits': self.ad_generator.extract_key_benefits(tweets_df[tweets_df['sentiment_score'] > 0]),
            'pain_points': self.ad_generator.identify_pain_points(tweets_df[tweets_df['sentiment_score'] < 0])
        }
        ai_suggestions = self.langflow_client.generate_ad_with_ai(context_data)
        return tweets_df, traditional_ad_ideas, ai_suggestions

def main():
    st.set_page_config(page_title="Advanced Twitter Analysis & Ad Generator", layout="wide")
    st.title("Twitter Analysis & AI-Powered Ad Generation")
    
    analyzer = TwitterAnalyzer()
    
    with st.sidebar:
        st.header("Configuration")
        query = st.text_input("Enter search query:")
        limit = st.number_input("Number of tweets to analyze:", min_value=10, max_value=100, value=50)
        
        if st.button("Analyze"):
            with st.spinner("Analyzing tweets and generating ad suggestions..."):
                tweets_df, traditional_ads, ai_ads = analyzer.fetch_and_analyze_tweets(query, limit)
                st.session_state['data'] = tweets_df
                st.session_state['traditional_ads'] = traditional_ads
                st.session_state['ai_ads'] = ai_ads

    if 'data' in st.session_state:
        st.dataframe(st.session_state['data'])

if __name__ == "__main__":
    main()
