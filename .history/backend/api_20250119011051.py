from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from database import AstraDB
from scrapers import DataScraper
from analyzer import InsightAnalyzer

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