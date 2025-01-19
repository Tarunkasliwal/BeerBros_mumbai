import requests
from bs4 import BeautifulSoup
import uuid
from datetime import datetime
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Cassandra Connection
def setup_cassandra_connection():
    cloud_config = {'secure_connect_bundle': '/path/to/secure-connect-database.zip'}
    auth_provider = PlainTextAuthProvider('client_id', 'client_secret')
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()
    session.set_keyspace('scraper')  # Replace with your keyspace name
    return session


# Function to Insert Data into Cassandra
def store_data(session, source, title, content, url):
    query = """
    INSERT INTO scraped_data (id, source, title, content, url, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    session.execute(query, (uuid.uuid4(), source, title, content, url, datetime.now()))


# Google Scraper
def scrape_google(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=10"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for g in soup.select(".tF2Cxc"):
        title = g.select_one(".DKV0Md").text
        link = g.select_one(".yuRUbf a")["href"]
        snippet = g.select_one(".VwiC3b").text if g.select_one(".VwiC3b") else ""
        results.append({"title": title, "link": link, "snippet": snippet})
    return results


# Reddit Scraper
def scrape_reddit(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.reddit.com/search/?q={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSou
