import sys
import json
from textblob import TextBlob
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import uuid

def analyze_data(scraped_data):
    data = json.loads(scraped_data)
    insights = {
        'positive': [],
        'negative': [],
        'neutral': []
    }

    for item in data:
        blob = TextBlob(item['snippet'])
        sentiment = blob.sentiment.polarity
        if sentiment > 0:
            insights['positive'].append(item)
        elif sentiment < 0:
            insights['negative'].append(item)
        else:
            insights['neutral'].append(item)

    # Save insights to Astra DB
    auth_provider = PlainTextAuthProvider(username='YOUR_USERNAME', password='YOUR_PASSWORD')
    cluster = Cluster(cloud={'secure_connect_bundle': 'C:\\path\\to\\secure-connect-bundle.zip'}, auth_provider=auth_provider)
    session = cluster.connect('your_keyspace')

    query = "INSERT INTO your_table (id, title, link, snippet, sentiment) VALUES (%s, %s, %s, %s, %s)"
    for item in data:
        sentiment = TextBlob(item['snippet']).sentiment.polarity
        session.execute(query, (uuid.uuid4(), item['title'], item['link'], item['snippet'], sentiment))

    session.shutdown()
    cluster.shutdown()

    return insights

if __name__ == "__main__":
    scraped_data = sys.argv[1]
    insights = analyze_data(scraped_data)
    print(json.dumps(insights))