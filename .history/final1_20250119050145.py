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
        st.dataframe(st.session_state["tweets_df"])

    if "ai_ads" in st.session_state and st.session_state["ai_ads"]:
        st.subheader("AI-Powered Ad Suggestions")
        for ad in st.session_state["ai_ads"]:
            st.write(ad)


if __name__ == "__main__":
    main()
