# utils.py
import requests
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import uuid
from config import TAVILIA_API_KEY, ASTRA_DB_SECURE_CONNECT_BUNDLE_PATH, ASTRA_DB_KEYSPACE

def fetch_tavilia_data(query):
    """Fetch data from Tavily API."""
    url = f'https://api.tavilia.com/search?q={query}&key={TAVILIA_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Tavily data: {response.status_code}")

def get_cassandra_session():
    """Connect to Astra DB and return the session."""
    cloud_config = {
        'secure_connect_bundle': ASTRA_DB_SECURE_CONNECT_BUNDLE_PATH
    }
    cluster = Cluster(cloud=cloud_config)
    session = cluster.connect()
    session.set_keyspace(ASTRA_DB_KEYSPACE)
    return session

def save_to_astra(session, data):
    """Save Tavily data to Astra DB."""
    insert_query = """
    INSERT INTO findings (id, title, score) VALUES (%s, %s, %s)
    """
    for item in data:
        session.execute(insert_query, (uuid.uuid4(), item['title'], item['relevance_score']))

def fetch_all_from_astra(session):
    """Fetch all data from Astra DB."""
    select_query = "SELECT * FROM findings"
    rows = session.execute(select_query)
    return [{'id': str(row.id), 'title': row.title, 'score': row.score} for row in rows]
