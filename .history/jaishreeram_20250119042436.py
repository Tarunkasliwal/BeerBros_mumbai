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
        """Generate ad ideas based on tweet analysis"""
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
        """Extract trending topics from tweets"""
        hashtags = []
        for text in tweets_df['text']:
            hashtags.extend(re.findall(r'#(\w+)', text))
        
        counter = Counter(hashtags)
        return [tag for tag, count in counter.most_common(5)]

    def extract_key_benefits(self, positive_tweets):
        """Extract key benefits from positive tweets"""
        benefits = []
        for text in positive_tweets['text']:
            blob = TextBlob(text)
            for sentence in blob.sentences:
                if any(word in sentence.lower() for word in ['great', 'amazing', 'love', 'perfect', 'best']):
                    benefits.append(str(sentence))
        return benefits[:5] if benefits else ["improved experience"]

    def identify_pain_points(self, negative_tweets):
        """Identify pain points from negative tweets"""
        pain_points = []
        for text in negative_tweets['text']:
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
        """Fetch tweets and create DataFrame"""
        tweets = []
        try:
            for tweet in tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics', 'lang']
            ).flatten(limit=limit):
                
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
        """Categorize sentiment score"""
        if score <= -0.05:
            return "negative"
        elif score >= 0.05:
            return "positive"
        else:
            return "neutral"

    def fetch_and_analyze_tweets(self, query, limit=100):
        """Fetch tweets and perform comprehensive analysis"""
        tweets_df = self.fetch_tweets(query, limit)
        
        traditional_ad_ideas = self.ad_generator.generate_ad_ideas(tweets_df)
        
        context_data = {
            'trending_topics': self.ad_generator.analyze_trending_topics(tweets_df),
            'sentiment': tweets_df['sentiment_score'].mean(),
            'benefits': self.ad_generator.extract_key_benefits(tweets_df[tweets_df['sentiment_score'] > 0]),
            'pain_points': self.ad_generator.identify_pain_points(tweets_df[tweets_df['sentiment_score'] < 0])
        }
        
        ai_suggestions = self.langflow_client.generate_ad_with_ai(context_data)
        
        return tweets_df, traditional_ad_ideas, ai_suggestions

    def generate_insights(self, tweets_df):
        """Generate insights from analyzed tweets"""
        insights = {
            'total_tweets': len(tweets_df),
            'sentiment_distribution': tweets_df['sentiment_category'].value_counts().to_dict(),
            'average_sentiment': tweets_df['sentiment_score'].mean(),
            'engagement_metrics': {
                'total_likes': tweets_df['likes'].sum(),
                'total_retweets': tweets_df['retweets'].sum(),
                'avg_likes_per_tweet': tweets_df['likes'].mean(),
                'avg_retweets_per_tweet': tweets_df['retweets'].mean()
            }
        }
        return insights

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
            st.header("Tweet Analysis Insights")
            insights = analyzer.generate_insights(st.session_state['data'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tweets Analyzed", insights['total_tweets'])
            with col2:
                st.metric("Average Sentiment", f"{insights['average_sentiment']:.2f}")
            with col3:
                st.metric("Total Engagement", 
                         insights['engagement_metrics']['total_likes'] + 
                         insights['engagement_metrics']['total_retweets'])
            
            st.subheader("Sentiment Distribution")
            fig = px.pie(values=list(insights['sentiment_distribution'].values()),
                        names=list(insights['sentiment_distribution'].keys()),
                        title="Sentiment Distribution")
            st.plotly_chart(fig)
        
        with tab2:
            st.header("Sentiment Analysis Over Time")
            fig = px.scatter(st.session_state['data'],
                           x='created_at',
                           y='sentiment_score',
                           color='sentiment_category',
                           title="Sentiment Score Timeline")
            st.plotly_chart(fig)
            
            st.subheader("Engagement by Sentiment")
            fig = px.box(st.session_state['data'],
                        x='sentiment_category',
                        y=['likes', 'retweets'],
                        title="Engagement Metrics by Sentiment")
            st.plotly_chart(fig)
        
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
            negative_tweets = st.session_state['data'][
                st.session_state['data']['sentiment_category'] == 'negative'
            ]
            
            if not negative_tweets.empty:
                st.warning(f"Found {len(negative_tweets)} tweets with negative sentiment")
                for _, tweet in negative_tweets.iterrows():
                    with st.expander(f"Tweet from {tweet['created_at']}"):
                        st.write(tweet['text'])
                        st.write(f"Sentiment Score: {tweet['sentiment_score']:.2f}")
                        st.write(f"Engagement: {tweet['likes']} likes, {tweet['retweets']} retweets")
            else:
                st.success("No negative tweets found in the analysis!")
        
        with tab5:
            st.header("Raw Data")
            st.dataframe(st.session_state['data'])

if __name__ == "__main__":
    main()