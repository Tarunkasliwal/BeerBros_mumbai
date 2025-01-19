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
from collections import Counter
import random

# Load environment variables
load_dotenv()

class AstraDBManager:
    def __init__(self):
        self.db = AstraDB(
            token=os.getenv('ASTRA_TOKEN'),
            api_endpoint=os.getenv('ASTRA_API_ENDPOINT'),
            namespace=os.getenv('ASTRA_KEYSPACE', 'twitter_analysis')
        )
        self.tweets_collection = self.db.collection('tweets')
        try:
            collections = self.db.get_collections()
            print(f"Connected to Astra DB: {collections}")
            if not self.tweets_collection:
                self.db.create_collection('tweets')
                self.tweets_collection = self.db.collection('tweets')
                print("Created 'tweets' collection")
        except Exception as e:
            print(f"Error connecting to Astra DB: {e}")

    def save_tweet(self, tweet_data):
        try:
            self.tweets_collection.insert_one(tweet_data)
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
        nltk.download('vader_lexicon')
        self.sia = SentimentIntensityAnalyzer()

    def fetch_tweets(self, query, limit=100):
        tweets = []
        response = self.client.search_recent_tweets(
            query=query,
            max_results=min(limit, 100),
            tweet_fields=['created_at', 'public_metrics', 'author_id']
        )
        if response.data:
            for tweet in response.data:
                sentiment = self.analyze_sentiment(tweet.text)
                tweet_data = {
                    'id': str(tweet.id),
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'author_id': str(tweet.author_id),
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'like_count': tweet.public_metrics['like_count'],
                    'reply_count': tweet.public_metrics['reply_count'],
                    'sentiment_score': sentiment['compound'],
                    'sentiment_category': self.get_sentiment_category(sentiment['compound']),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                tweets.append(tweet_data)
                self.db_manager.save_tweet(tweet_data)
        return pd.DataFrame(tweets)

    def analyze_sentiment(self, text):
        return self.sia.polarity_scores(text)

    def get_sentiment_category(self, compound_score):
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'

    def analyze_content_issues(self, text):
        text_lower = text.lower()
        issues = []
        toxic_keywords = ['hate', 'awful', 'terrible', 'worst', 'stupid']
        misinfo_keywords = ['fake', 'hoax', 'conspiracy', 'false']
        critical_keywords = ['urgent', 'emergency', 'crisis', 'failure']

        if any(word in text_lower for word in toxic_keywords):
            issues.append('toxicity')
        if any(word in text_lower for word in misinfo_keywords):
            issues.append('misinformation')
        if any(word in text_lower for word in critical_keywords):
            issues.append('critical_issues')

        return issues if issues else ['general_negative']

    def generate_damage_control_suggestions(self, tweet):
        issues = self.analyze_content_issues(tweet['text'])
        suggestions = {
            'toxicity': [
                "Respond professionally",
                "Report if against guidelines",
                "Engage constructively"
            ],
            'misinformation': [
                "Share verified sources",
                "Request fact-checking",
                "Prepare an informative thread"
            ],
            'critical_issues': [
                "Escalate to team",
                "Draft an official response",
                "Monitor hashtags"
            ],
            'general_negative': [
                "Acknowledge concerns",
                "Provide helpful info",
                "Offer DM support"
            ]
        }
        return [s for issue in issues for s in suggestions.get(issue, [])]

class AdGenerator:
    def __init__(self):
        self.positive_templates = [
            "Experience what everyone's talking about! {benefit}",
            "Join the conversation! {benefit}",
            "Discover why {benefit} matters"
        ]
        self.response_templates = [
            "We hear you! That's why we {solution}",
            "Your concerns matter. See how we {solution}"
        ]

    def analyze_trending_topics(self, tweets_df):
        all_text = ' '.join(tweets_df['text'].astype(str))
        words = [word.lower() for word in all_text.split() if len(word) > 3]
        word_freq = Counter(words)
        return [word for word, count in word_freq.most_common(5)]

    def extract_key_benefits(self, positive_tweets_df):
        positive_words = []
        for text in positive_tweets_df['text']:
            words = str(text).lower().split()
            for i, word in enumerate(words):
                if word in {'great', 'amazing', 'excellent'}:
                    if i + 1 < len(words):
                        positive_words.append(words[i + 1])
        return Counter(positive_words).most_common(5)

    def identify_pain_points(self, negative_tweets_df):
        pain_points = []
        for text in negative_tweets_df['text']:
            words = str(text).lower().split()
            for i, word in enumerate(words):
                if word in {'bad', 'poor', 'terrible'}:
                    if i + 1 < len(words):
                        pain_points.append(words[i + 1])
        return Counter(pain_points).most_common(5)

    def generate_ad_ideas(self, tweets_df):
        positive_tweets = tweets_df[tweets_df['sentiment_score'] > 0.2]
        negative_tweets = tweets_df[tweets_df['sentiment_score'] < -0.2]
        trending = self.analyze_trending_topics(tweets_df)
        benefits = self.extract_key_benefits(positive_tweets)
        pain_points = self.identify_pain_points(negative_tweets)
        ad_ideas = []
        for benefit, _ in benefits:
            template = random.choice(self.positive_templates)
            ad_ideas.append(template.format(benefit=benefit))
        for pain_point, _ in pain_points:
            template = random.choice(self.response_templates)
            solution = f"provide better {pain_point}"
            ad_ideas.append(template.format(solution=solution))
        return ad_ideas

def main():
    st.set_page_config(page_title="Twitter Analysis Tool", layout="wide")
    st.title("Twitter Sentiment and Ad Insights")

    analyzer = TwitterAnalyzer()
    ad_generator = AdGenerator()

    with st.sidebar:
        st.header("Configuration")
        query = st.text_input("Enter search query:")
        limit = st.number_input("Number of tweets to analyze:", min_value=5, max_value=100, value=50)

        if st.button("Analyze"):
            with st.spinner("Analyzing tweets..."):
                df = analyzer.fetch_tweets(query, limit)
                st.session_state['data'] = df

    if 'data' in st.session_state:
        df = st.session_state['data']

        tab1, tab2, tab3 = st.tabs(["Sentiment Analysis", "Damage Control", "Ad Ideas"])

        with tab1:
            st.header("Sentiment Analysis")
            fig = px.histogram(df, x='sentiment_score', nbins=20, title='Sentiment Distribution')
            st.plotly_chart(fig)

        with tab2:
            st.header("Damage Control Suggestions")
            flagged_tweets = analyzer.db_manager.get_flagged_tweets()
            if not flagged_tweets.empty:
                for _, tweet in flagged_tweets.iterrows():
                    st.subheader(f"Tweet ID: {tweet['id']}")
                    st.write(f"Tweet: {tweet['text']}")
                    suggestions = analyzer.generate_damage_control_suggestions(tweet)
                    st.write("Suggested Actions:")
                    for suggestion in suggestions:
                        st.write(f"- {suggestion}")
            else:
                st.write("No flagged tweets found.")

        with tab3:
            st.header("Ad Generation Ideas")
            ad_ideas = ad_generator.generate_ad_ideas(df)
            if ad_ideas:
                for idx, ad in enumerate(ad_ideas, 1):
                    st.subheader(f"Ad Idea {idx}")
                    st.write(ad)
            else:
                st.write("No ad ideas generated.")

if __name__ == "__main__":
    main()

           
