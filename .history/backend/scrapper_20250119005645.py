from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re

class DataScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.sia = SentimentIntensityAnalyzer()

    def clean_text(self, text):
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        return text

    def scrape_youtube_no_api(self, query, max_results=50):
        data = []
        search_url = f'https://www.youtube.com/results?search_query={query}'
        
        self.driver.get(search_url)
        time.sleep(3)  # Allow dynamic content to load
        
        # Scroll to load more videos
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
        
        video_elements = self.driver.find_elements(By.CSS_SELECTOR, '#video-title')
        
        for element in video_elements[:max_results]:
            try:
                title = element.get_attribute('title')
                description = element.get_attribute('aria-label')
                
                if title and description:
                    content = f"{title} {description}"
                    clean_content = self.clean_text(content)
                    sentiment = self.sia.polarity_scores(clean_content)['compound']
                    
                    data.append({
                        'source': 'youtube',
                        'content': clean_content,
                        'sentiment': sentiment
                    })
            except:
                continue
                
        return data

    def scrape_reddit_no_api(self, query, max_results=50):
        data = []
        search_url = f'https://www.reddit.com/search/?q={query}'
        
        self.driver.get(search_url)
        time.sleep(3)
        
        # Scroll to load more posts
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
        
        posts = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="post-container"]')
        
        for post in posts[:max_results]:
            try:
                title = post.find_element(By.CSS_SELECTOR, 'h3').text
                # Try to get post content if available
                try:
                    content = post.find_element(By.CSS_SELECTOR, '[data-click-id="text"]').text
                except:
                    content = ""
                
                full_content = f"{title} {content}"
                clean_content = self.clean_text(full_content)
                sentiment = self.sia.polarity_scores(clean_content)['compound']
                
                data.append({
                    'source': 'reddit',
                    'content': clean_content,
                    'sentiment': sentiment
                })
            except:
                continue
                
        return data

    def scrape_quora_no_api(self, query, max_results=50):
        data = []
        search_url = f'https://www.quora.com/search?q={query}'
        
        self.driver.get(search_url)
        time.sleep(3)
        
        # Scroll to load more content
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
        
        answers = self.driver.find_elements(By.CSS_SELECTOR, '.q-box.qu-pt--medium')
        
        for answer in answers[:max_results]:
            try:
                content = answer.text
                clean_content = self.clean_text(content)
                sentiment = self.sia.polarity_scores(clean_content)['compound']
                
                data.append({
                    'source': 'quora',
                    'content': clean_content,
                    'sentiment': sentiment
                })
            except:
                continue
                
        return data

    def __del__(self):
        self.driver.quit()