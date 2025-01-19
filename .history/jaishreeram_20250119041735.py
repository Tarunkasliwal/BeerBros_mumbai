import streamlit as st
import tweepy
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from astrapy.db import AstraDB
import requests
from typing import Optional
import warnings

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
            result = self.tweets_collection.insert_one(tweet_data)
            return True
        except Exception as e:
            print(f"Error saving tweet: {e}")
            return False
    
    def get_flagged_tweets(self):
        try:
            cursor = self.tweets_collection.find({"sentiment_category": "negative"})
            return pd.DataFrame(cursor)
        except Exception as e:
            print(f"Error retrieving flagged tweets: {e}")
            return pd.DataFrame()

class LangFlowClient:
    def __init__(self):
        self.base_url = BASE_API_URL
        self.langflow_id = LANGFLOW_ID
        self.application_token = APPLICATION_TOKEN

    def generate_ad_with_ai(self, context_data, endpoint=FLOW_ID):
        """Generate AI-powered ad suggestions using LangFlow"""
        api_url = f"{self.base_url}/lf/{self.langflow_id}/api/v1/run/{endpoint}"
        
        # Prepare context for AI
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
    def generate_ad_ideas(self, tweets_df):
        # Placeholder for generating ad ideas
        ad_ideas = []
        for _, row in tweets_df.iterrows():
            ad_ideas.append({
                "type": "Promotional",
                "content": f"Check out our product! People are talking about {row['text']}",
                "target_emotion": "Excitement",
                "trending_topic": row['hashtags'][0] if row['hashtags'] else "General"
            })
        return ad_ideas

    def analyze_trending_topics(self, tweets_df):
        # Placeholder for analyzing trending topics
        return tweets_df['hashtags'].explode().value_counts().head(5).index.tolist()

    def extract_key_benefits(self, positive_tweets_df):
        # Placeholder for extracting key benefits
        return ["Benefit 1", "Benefit 2"]

    def identify_pain_points(self, negative_tweets_df):
        # Placeholder for identifying pain points
        return ["Pain Point 1", "Pain Point 2"]

class CreativeAssetGenerator:
    # Placeholder for CreativeAssetGenerator
    pass

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
        """Fetch tweets using Tweepy"""
        try:
            tweets = self.client.search_recent_tweets(query=query, max_results=limit, tweet_fields=['created_at', 'entities'])
            tweets_df = pd.DataFrame([tweet.data for tweet in tweets.data])
            tweets_df['sentiment_score'] = tweets_df['text'].apply(lambda x: self.sia.polarity_scores(x)['compound'])
            tweets_df['sentiment_category'] = tweets_df['sentiment_score'].apply(lambda x: 'positive' if x > 0 else ('negative' if x < 0 else 'neutral'))
            tweets_df['hashtags'] = tweets_df['entities'].apply(lambda x: [hashtag['tag'] for hashtag in x['hashtags']] if x and 'hashtags' in x else [])
            return tweets_df
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return pd.DataFrame()

    def fetch_and_analyze_tweets(self, query, limit=100):
        """Fetch tweets and perform comprehensive analysis"""
        tweets_df = self.fetch_tweets(query, limit)
        
        # Generate traditional ad ideas
        traditional_ad_ideas = self.ad_generator.generate_ad_ideas(tweets_df)
        
        # Prepare context for AI ad generation
        context_data = {
            'trending_topics': self.ad_generator.analyze_trending_topics(tweets_df),
            'sentiment': tweets_df['sentiment_score'].mean(),
            'benefits': self.ad_generator.extract_key_benefits(tweets_df[tweets_df['sentiment_score'] > 0]),
            'pain_points': self.ad_generator.identify_pain_points(tweets_df[tweets_df['sentiment_score'] < 0])
        }
        
        # Generate AI-powered ad suggestions
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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Insights", "Sentiment Analysis", "Ad Suggestions", "Damage Control", "Raw Data"])
    
    if 'data' in st.session_state:
        with tab1:
            st.header("Insights")
            st.write("Here you can display overall insights from the analyzed tweets.")
        
        with tab2:
            st.header("Sentiment Analysis")
            st.write("Here you can display sentiment analysis results.")
        
        with tab3:
            st.header("Ad Suggestions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("AI-Generated Ads")
                if 'ai_ads' in st.session_state and st.session_state['ai_ads']:
                    for msg in st.session_state['ai_ads'].get('messages', []):
                        st.write(msg.get('message', ''))
            
            with col2:
                st.subheader("Template-Based Ads")
                if 'traditional_ads' in st.session_state:
                    for ad in st.session_state['traditional_ads']:
                        with st.expander(f"Ad Idea: {ad['type']}"):
                            st.write(f"Content: {ad['content']}")
                            st.write(f"Target Emotion: {ad['target_emotion']}")
                            st.write(f"Trending Topic: #{ad['trending_topic']}")
        
        with tab4:
            st.header("Damage Control")
            st.write("Here you can address negative sentiment and take corrective actions.")
        
        with tab5:
            st.header("Raw Data")
            st.dataframe(st.session_state['data'])

if __name__ == "__main__":
    main()