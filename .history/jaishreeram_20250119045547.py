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
from astrapy.db import AstraDB  # Correct import

# Load environment variables
load_dotenv()

class AstraDBManager:
    def _init_(self):
        # Initialize AstraDB client directly
        self.db = AstraDB(
            token=os.getenv('ASTRA_TOKEN'),
            api_endpoint=os.getenv('ASTRA_API_ENDPOINT'),
            namespace=os.getenv('ASTRA_KEYSPACE', 'default_keyspace')
        )
        
        # Initialize the collection
        self.tweets_collection = self.db.collection('tweets')
        
        # Verify connection
        try:
            collections = self.db.get_collections()
            print(f"Connected to Astra DB: {collections}")
            
            # Create collection if it doesn't exist
            if not self.tweets_collection:
                self.db.create_collection('tweets')
                self.tweets_collection = self.db.collection('tweets')
                print("Created 'tweets' collection")
        except Exception as e:
            print(f"Error connecting to Astra DB: {e}")
    
    def save_tweet(self, tweet_data):
        """Save tweet data to Astra DB"""
        try:
            result = self.tweets_collection.insert_one(tweet_data)
            return True
        except Exception as e:
            print(f"Error saving tweet: {e}")
            return False
    
    def get_flagged_tweets(self):
        """Retrieve flagged tweets from database"""
        try:
            cursor = self.tweets_collection.find({"sentiment_category": "negative"})
            return pd.DataFrame(cursor)
        except Exception as e:
            print(f"Error retrieving flagged tweets: {e}")
            return pd.DataFrame()

class TwitterAnalyzer:
    def _init_(self):
        # Initialize Twitter API client
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        # Initialize Astra DB
        self.db_manager = AstraDBManager()
        
        # Initialize NLTK
        nltk.download('vader_lexicon')
        self.sia = SentimentIntensityAnalyzer()
    
    def fetch_tweets(self, query, limit=100):
        """Fetch tweets for a given query"""
        tweets = []
        
        # Search tweets using Twitter API v2
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
        """Analyze sentiment of text using VADER"""
        return self.sia.polarity_scores(text)
    
    def get_sentiment_category(self, compound_score):
        """Categorize sentiment based on compound score"""
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_content_issues(self, text):
        """Analyze content for specific issues"""
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
        """Generate damage control suggestions based on tweet content"""
        issues = self.analyze_content_issues(tweet['text'])
        
        suggestions = {
            'toxicity': [
                "Respond with a professional and calm message",
                "Report tweet if it violates Twitter's guidelines",
                "Engage constructively with the author"
            ],
            'misinformation': [
                "Share verified sources and correct information",
                "Request fact-checking",
                "Prepare an informative thread with accurate data"
            ],
            'critical_issues': [
                "Escalate to social media team",
                "Draft official response",
                "Monitor related hashtags and conversations"
            ],
            'general_negative': [
                "Acknowledge the concern",
                "Provide helpful information",
                "Offer to continue conversation in DMs"
            ]
        }
        
        return [suggestion for issue in issues for suggestion in suggestions.get(issue, [])]

def main():
    st.set_page_config(page_title="ART", layout="wide")
    st.title("ART WITH DAMAGE CONTROL FOR EVERYONE")
    
    analyzer = TwitterAnalyzer()
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        query = st.text_input("Enter search query:")
        limit = st.number_input("Number of tweets to analyze:", min_value=5, max_value=10, value=10)
        
        if st.button("Analyze"):
            with st.spinner("Analyzing tweets..."):
                df = analyzer.fetch_tweets(query, limit)
                st.session_state['data'] = df
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["Insights", "Sentiment Analysis", "Damage Control", "Raw Data"])
    
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        with tab1:
            st.header("Insights")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Sentiment", f"{df['sentiment_score'].mean():.2f}")
            with col2:
                st.metric("Positive Tweets", len(df[df['sentiment_category'] == 'positive']))
            with col3:
                st.metric("Negative Tweets", len(df[df['sentiment_category'] == 'negative']))
                
            # Engagement metrics
            st.subheader("Engagement Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Retweets", df['retweet_count'].sum())
            with col2:
                st.metric("Total Likes", df['like_count'].sum())
            with col3:
                st.metric("Total Replies", df['reply_count'].sum())
        
        with tab2:
            st.header("Sentiment Analysis")
            fig = px.histogram(df, x='sentiment_score', nbins=20,
                             title='Sentiment Distribution')
            st.plotly_chart(fig)
            
            gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = df['sentiment_score'].mean(),
                title = {'text': "Average Sentiment"},
                gauge = {'axis': {'range': [-1, 1]}}
            ))
            st.plotly_chart(gauge)
            
            df['created_at'] = pd.to_datetime(df['created_at'])
            fig = px.line(df.sort_values('created_at'), 
                         x='created_at', 
                         y='sentiment_score',
                         title='Sentiment Trend Over Time')
            st.plotly_chart(fig)
        
        with tab3:
            st.header("Damage Control")
            negative_tweets = df[df['sentiment_category'] == 'negative']
            
            for _, tweet in negative_tweets.iterrows():
                with st.expander(f"🚨 Tweet from {tweet['author_id']}"):
                    st.write(tweet['text'])
                    st.write(f"Sentiment Score: {tweet['sentiment_score']:.2f}")
                    st.write(f"Engagement: {tweet['retweet_count']} RTs, {tweet['like_count']} Likes")
                    
                    st.write("Suggested Actions:")
                    for suggestion in analyzer.generate_damage_control_suggestions(tweet):
                        st.write(f"- {suggestion}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.button("Respond", key=f"respond_{tweet['id']}")
                    with col2:
                        st.button("Monitor", key=f"monitor_{tweet['id']}")
                    with col3:
                        st.button("Report", key=f"report_{tweet['id']}")
        
        with tab4:
            st.header("Raw Data")
            st.dataframe(df)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="twitter_analysis.csv",
                mime="text/csv"
            )
class AdGenerator:
    def _init_(self):
        self.positive_templates = [
            "Experience what everyone's talking about! {benefit}",
            "Join the conversation! {benefit}",
            "The solution you've been looking for: {benefit}",
            "Why people love us: {benefit}",
            "Discover why {benefit} matters"
        ]
        
        self.response_templates = [
            "We hear you! That's why we {solution}",
            "Looking for better? We {solution}",
            "Your concerns matter. See how we {solution}",
            "Ready for a change? We {solution}",
            "Time for an upgrade? Discover how we {solution}"
        ]
        
    def analyze_trending_topics(self, tweets_df):
        """Extract trending topics and keywords from tweets"""
        # Combine all tweet text
        all_text = ' '.join(tweets_df['text'].astype(str))
        
        # Remove common words and special characters
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        words = [word.lower() for word in all_text.split() 
                if word.lower() not in common_words and len(word) > 3]
        
        # Count word frequencies
        from collections import Counter
        word_freq = Counter(words)
        
        # Get top trending topics
        trending_topics = [word for word, count in word_freq.most_common(5)]
        return trending_topics
    
    def extract_key_benefits(self, positive_tweets_df):
        """Extract key benefits and positive aspects from tweets"""
        positive_words = []
        for text in positive_tweets_df['text']:
            # Simple extraction of adjectives and nouns after positive words
            words = str(text).lower().split()
            for i, word in enumerate(words):
                if word in {'great', 'amazing', 'excellent', 'best', 'love', 'perfect'}:
                    if i + 1 < len(words):
                        positive_words.append(words[i + 1])
        
        # Get most common positive aspects
        from collections import Counter
        return Counter(positive_words).most_common(5)
    
    def identify_pain_points(self, negative_tweets_df):
        """Extract pain points and concerns from negative tweets"""
        pain_points = []
        for text in negative_tweets_df['text']:
            # Extract issues after negative sentiment words
            words = str(text).lower().split()
            for i, word in enumerate(words):
                if word in {'bad', 'poor', 'terrible', 'worst', 'hate', 'difficult', 'problem'}:
                    if i + 1 < len(words):
                        pain_points.append(words[i + 1])
        
        return Counter(pain_points).most_common(5)
    
    def generate_ad_ideas(self, tweets_df):
        """Generate ad ideas based on tweet analysis"""
        import random
        
        # Separate positive and negative tweets
        positive_tweets = tweets_df[tweets_df['sentiment_score'] > 0.2]
        negative_tweets = tweets_df[tweets_df['sentiment_score'] < -0.2]
        
        # Get trending topics
        trending = self.analyze_trending_topics(tweets_df)
        
        # Extract benefits and pain points
        benefits = self.extract_key_benefits(positive_tweets)
        pain_points = self.identify_pain_points(negative_tweets)
        
        ad_ideas = []
        
        # Generate positive message ads
        for benefit, _ in benefits:
            template = random.choice(self.positive_templates)
            ad_ideas.append({
                'type': 'positive_message',
                'content': template.format(benefit=benefit),
                'target_emotion': 'positive',
                'trending_topic': random.choice(trending),
                'benefit_highlighted': benefit
            })
        
        # Generate response ads addressing pain points
        for pain_point, _ in pain_points:
            template = random.choice(self.response_templates)
            solution = f"provide {random.choice(['better', 'improved', 'enhanced'])} {pain_point}"
            ad_ideas.append({
                'type': 'pain_point_response',
                'content': template.format(solution=solution),
                'target_emotion': 'solution_oriented',
                'pain_point_addressed': pain_point,
                'trending_topic': random.choice(trending)
            })
        
        return ad_ideas

class CreativeAssetGenerator:
    def _init_(self):
        self.color_schemes = {
            'positive': ['#4CAF50', '#81C784', '#C8E6C9'],  # Green shades
            'solution_oriented': ['#2196F3', '#64B5F6', '#BBDEFB'],  # Blue shades
        }
        
    def generate_ad_visual(self, ad_idea):
        """Generate a visual representation of the ad"""
        colors = self.color_schemes[ad_idea['target_emotion']]
        
        # Create an SVG for the ad
        svg_content = self.create_ad_svg(ad_idea, colors)
        return svg_content
    
    def create_ad_svg(self, ad_idea, colors):
        """Create an SVG visualization for the ad"""
        return f'''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <!-- Background -->
            <rect width="400" height="300" fill="{colors[2]}" />
            
            <!-- Header Bar -->
            <rect width="400" height="60" fill="{colors[0]}" />
            
            <!-- Main Content Area -->
            <foreignObject x="20" y="80" width="360" height="180">
                <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: Arial; color: #333;">
                    <h2 style="color: {colors[0]};">{ad_idea['content']}</h2>
                    <p>Trending: #{ad_idea['trending_topic']}</p>
                </div>
            </foreignObject>
            
            <!-- Footer Bar -->
            <rect y="260" width="400" height="40" fill="{colors[1]}" />
        </svg>
        '''
        
if _name_ == "_main_":
    main()