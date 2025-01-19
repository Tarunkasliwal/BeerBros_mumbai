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
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for post in soup.select(".Post"):
        title = post.select_one("h3").text if post.select_one("h3") else ""
        link = post.select_one("a")["href"] if post.select_one("a") else ""
        snippet = post.select_one("p").text if post.select_one("p") else ""
        results.append({"title": title, "link": f"https://www.reddit.com{link}", "snippet": snippet})
    return results


# YouTube Scraper
def scrape_youtube(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for video in soup.select(".yt-simple-endpoint.style-scope.ytd-video-renderer"):
        title = video["title"]
        link = f"https://www.youtube.com{video['href']}"
        results.append({"title": title, "link": link})
    return results


# Main Function
def main():
    # Query
    query = "AI in marketing"

    # Cassandra Setup
    session = setup_cassandra_connection()

    # Scrape Google
    print("Scraping Google...")
    google_data = scrape_google(query)
    for item in google_data:
        store_data(session, "Google", item["title"], item["snippet"], item["link"])

    # Scrape Reddit
    print("Scraping Reddit...")
    reddit_data = scrape_reddit(query)
    for item in reddit_data:
        store_data(session, "Reddit", item["title"], item["snippet"], item["link"])

    # Scrape YouTube
    print("Scraping YouTube...")
    youtube_data = scrape_youtube(query)
    for item in youtube_data:
        store_data(session, "YouTube", item["title"], "", item["link"])

    print("Scraping completed and data stored in Astra DB.")


if __name__ == "__main__":
    main()
