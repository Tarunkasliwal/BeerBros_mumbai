import pandas as pd
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

class InsightAnalyzer:
    def __init__(self):
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('vader_lexicon')
        self.stop_words = set(stopwords.words('english'))

    def extract_triggers(self, text):
        tokens = word_tokenize(text.lower())
        tokens = [t for t in tokens if t not in self.stop_words and t.isalnum()]
        return tokens

    def analyze_data(self, raw_data):
        all_triggers = []
        for item in raw_data:
            triggers = self.extract_triggers(item['content'])
            all_triggers.extend(triggers)

        trigger_freq = Counter(all_triggers)
        insights = []
        
        for trigger, freq in trigger_freq.most_common(20):
            relevant_content = [
                item for item in raw_data 
                if trigger in item['content'].lower()
            ]
            avg_sentiment = sum(item['sentiment'] for item in relevant_content) / len(relevant_content)
            
            insights.append({
                'trigger': trigger,
                'frequency': freq,
                'sentiment': avg_sentiment
            })
            
        return insights

# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI()
db = AstraDB()
scraper = DataScraper()
analyzer = InsightAnalyzer()

class ResearchRequest(BaseModel):
    topic: str
    max_results: Optional[int] = 50

class Insight(BaseModel):
    trigger: str
    frequency: int
    sentiment: float

@app.post("/research", response_model=List[Insight])
async def research_topic(request: ResearchRequest):
    # Gather data from different sources
    youtube_data = scraper.scrape_youtube_no_api(request.topic, request.max_results)
    reddit_data = scraper.scrape_reddit_no_api(request.topic, request.max_results)
    quora_data = scraper.scrape_quora_no_api(request.topic, request.max_results)
    
    # Store raw data
    all_data = youtube_data + reddit_data + quora_data
    for item in all_data:
        db.insert_raw_data(
            item['source'],
            item['content'],
            item['sentiment'],
            request.topic
        )
    
    # Analyze and store insights
    insights = analyzer.analyze_data(all_data)
    for insight in insights:
        db.insert_insight(
            request.topic,
            insight['trigger'],
            insight['frequency'],
            insight['sentiment'],
            set()
        )
    
    return insights

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)