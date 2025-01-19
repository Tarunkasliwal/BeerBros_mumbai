# utils.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TAVILIA_API_KEY

def fetch_reddit_data(subreddit):
    url = f'https://oauth.reddit.com/r/{subreddit}/new.json?limit=10'
    headers = {'User-Agent': 'Mozilla/5.0'}
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {'grant_type': 'client_credentials'}
    res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
    TOKEN = res.json()['access_token']
    headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}} 
    response = requests.get(url, headers=headers)
    return response.json()

def fetch_tavilia_data(query):
    url = f'https://api.tavilia.com/search?q={query}&key={TAVILIA_API_KEY}'
    response = requests.get(url)
    return response.json()