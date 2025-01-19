import streamlit as st
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from serpapi.google_search import GoogleSearchfrom collections import Counter
import random

# Load environment variables
load_dotenv()

class SearchAnalyzer:
    def _init_(self):
        self.serpapi_key = os.getenv('03c96cdc4bf9e2ecce3ae82c69d2414c7c432d625ce33f3ec2fcea745d772337')
        nltk.download('vader_lexicon')
        self.sia = SentimentIntensityAnalyzer()
        
    def fetch_data(self, query, limit=100):
        results = []
        
        # Search Google
        search_params = {
            "q": query,
            "api_key": self.serpapi_key,
            "engine": "google",
            "num": min(limit, 100),
            "tbm": "nws"  # News results
        }
        
        try:
            search = GoogleSearch(search_params)
            news_results = search.get_dict().get('news_results', [])
            
            for result in news_results:
                sentiment = self.analyze_sentiment(result.get('snippet', ''))
                result_data = {
                    'id': result.get('position', ''),
                    'title': result.get('title', ''),
                    'text': result.get('snippet', ''),
                    'source': result.get('source', ''),
                    'date': result.get('date', ''),
                    'link': result.get('link', ''),
                    'sentiment_score': sentiment['compound'],
                    'sentiment_category': self.get_sentiment_category(sentiment['compound']),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                results.append(result_data)
                
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            
        return pd.DataFrame(results)
    
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
    
    def generate_damage_control_suggestions(self, content):
        issues = self.analyze_content_issues(content['text'])
        
        suggestions = {
            'toxicity': [
                "Prepare a professional response addressing concerns",
                "Create positive content to counter negative narratives",
                "Engage with credible industry experts"
            ],
            'misinformation': [
                "Publish fact-based content with verified sources",
                "Create an educational campaign",
                "Partner with trusted authorities in the field"
            ],
            'critical_issues': [
                "Develop a crisis communication plan",
                "Prepare detailed FAQ and response documents",
                "Monitor related news and social media coverage"
            ],
            'general_negative': [
                "Create content addressing common concerns",
                "Highlight positive aspects and improvements",
                "Develop proactive communication strategy"
            ]
        }
        
        return [suggestion for issue in issues for suggestion in suggestions.get(issue, [])]

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
    
    def analyze_trending_topics(self, data_df):
        all_text = ' '.join(data_df['text'].astype(str))
        
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        words = [word.lower() for word in all_text.split() 
                if word.lower() not in common_words and len(word) > 3]
        
        word_freq = Counter(words)
        return [word for word, count in word_freq.most_common(5)]
    
    def generate_ad_ideas(self, data_df):
        positive_content = data_df[data_df['sentiment_score'] > 0.2]
        negative_content = data_df[data_df['sentiment_score'] < -0.2]
        
        trending = self.analyze_trending_topics(data_df)
        
        ad_ideas = []
        
        # Generate positive ads
        for _, content in positive_content.head().iterrows():
            template = random.choice(self.positive_templates)
            benefit = ' '.join(content['title'].split()[:3])  # Use first few words of title
            ad_ideas.append({
                'type': 'positive_message',
                'content': template.format(benefit=benefit),
                'target_emotion': 'positive',
                'trending_topic': random.choice(trending),
                'benefit_highlighted': benefit
            })
        
        # Generate response ads
        for _, content in negative_content.head().iterrows():
            template = random.choice(self.response_templates)
            solution = f"provide {random.choice(['better', 'improved', 'enhanced'])} solutions"
            ad_ideas.append({
                'type': 'pain_point_response',
                'content': template.format(solution=solution),
                'target_emotion': 'solution_oriented',
                'pain_point_addressed': content['text'][:50] + "...",
                'trending_topic': random.choice(trending)
            })
        
        return ad_ideas

def main():
    st.set_page_config(page_title="ART", layout="wide")
    st.title("ART WITH DAMAGE CONTROL AND AI-POWERED AD GENERATION")
    
    analyzer = SearchAnalyzer()
    ad_generator = AdGenerator()
    
    with st.sidebar:
        st.header("Configuration")
        
        st.subheader("Company Information")
        company_info = {
            'name': st.text_input("Company Name", "Your Company"),
            'type': st.text_input("Company Type", "Tech Company"),
            'target_audience': st.text_input("Target Audience", "Gen Z and Millennials"),
            'key_points': st.text_area("Key Selling Points", "Innovation, Quality, Affordability"),
            'platforms': st.multiselect(
                "Target Platforms",
                ["Instagram", "TikTok", "Facebook", "LinkedIn"],
                default=["Instagram", "TikTok"]
            )
        }
        
        query = st.text_input("Enter search query:")
        limit = st.number_input("Number of results to analyze:", min_value=10, max_value=100, value=50)
        
        if st.button("Analyze"):
            with st.spinner("Analyzing data and generating insights..."):
                df = analyzer.fetch_data(query, limit)
                st.session_state['data'] = df
                
                # Generate ad ideas
                ad_ideas = ad_generator.generate_ad_ideas(df)
                st.session_state['ad_ideas'] = ad_ideas
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Insights", "Sentiment Analysis", "Damage Control", "Ad Suggestions"
    ])
    
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        with tab1:
            st.header("Insights")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Sentiment", f"{df['sentiment_score'].mean():.2f}")
            with col2:
                st.metric("Positive Content", len(df[df['sentiment_category'] == 'positive']))
            with col3:
                st.metric("Negative Content", len(df[df['sentiment_category'] == 'negative']))
            
            st.subheader("Recent Content Analysis")
            for _, content in df.head().iterrows():
                with st.expander(f"📰 {content['title']}"):
                    st.write(f"Source: {content['source']}")
                    st.write(f"Date: {content['date']}")
                    st.write(content['text'])
                    st.write(f"Sentiment: {content['sentiment_score']:.2f}")
        
        with tab2:
            st.header("Sentiment Analysis")
            
            # Sentiment distribution
            fig = px.histogram(df, x='sentiment_score', nbins=20,
                             title='Sentiment Distribution')
            st.plotly_chart(fig)
            
            # Sentiment gauge
            gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = df['sentiment_score'].mean(),
                title = {'text': "Average Sentiment"},
                gauge = {'axis': {'range': [-1, 1]}}
            ))
            st.plotly_chart(gauge)
            
            # Source sentiment analysis
            source_sentiment = df.groupby('source')['sentiment_score'].mean().reset_index()
            fig = px.bar(source_sentiment, x='source', y='sentiment_score',
                        title='Average Sentiment by Source')
            st.plotly_chart(fig)
        
        with tab3:
            st.header("Damage Control")
            negative_content = df[df['sentiment_category'] == 'negative']
            
            for _, content in negative_content.iterrows():
                with st.expander(f"⚠️ {content['title']}"):
                    st.write(f"Source: {content['source']}")
                    st.write(content['text'])
                    st.write(f"Sentiment Score: {content['sentiment_score']:.2f}")
                    
                    st.write("Suggested Actions:")
                    for suggestion in analyzer.generate_damage_control_suggestions(content):
                        st.write(f"- {suggestion}")
        
        with tab4:
            st.header("Ad Suggestions")
            
            if 'ad_ideas' in st.session_state:
                for i, ad in enumerate(st.session_state['ad_ideas'], 1):
                    with st.expander(f"💡 Ad Idea {i}: {ad['type'].replace('_', ' ').title()}"):
                        st.write(f"*Content:* {ad['content']}")
                        st.write(f"*Target Emotion:* {ad['target_emotion']}")
                        st.write(f"*Trending Topic:* #{ad['trending_topic']}")
                        if 'benefit_highlighted' in ad:
                            st.write(f"*Key Benefit:* {ad['benefit_highlighted']}")
                        if 'pain_point_addressed' in ad:
                            st.write(f"*Addressing:* {ad['pain_point_addressed']}")

if __name__ == "_main_":
    main()