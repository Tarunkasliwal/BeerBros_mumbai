from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime

class AstraDB:
    def __init__(self):
        cloud_config = {
            'secure_connect_bundle': ASTRA_DB_SECURE_BUNDLE_PATH
        }
        auth_provider = PlainTextAuthProvider(
            ASTRA_DB_CLIENT_ID,
            ASTRA_DB_CLIENT_SECRET
        )
        self.cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        self.session = self.cluster.connect(ASTRA_DB_KEYSPACE)
        self._create_tables()

    def _create_tables(self):
        # Table for storing raw data
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS raw_data (
                id uuid PRIMARY KEY,
                source text,
                content text,
                sentiment float,
                created_at timestamp,
                topic text
            )
        """)

        # Table for storing analyzed insights
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id uuid PRIMARY KEY,
                topic text,
                trigger text,
                frequency int,
                sentiment float,
                source_ids set<uuid>,
                created_at timestamp
            )
        """)

    def insert_raw_data(self, source, content, sentiment, topic):
        query = """
            INSERT INTO raw_data (id, source, content, sentiment, created_at, topic)
            VALUES (uuid(), %s, %s, %s, %s, %s)
        """
        self.session.execute(query, (source, content, sentiment, datetime.now(), topic))

    def insert_insight(self, topic, trigger, frequency, sentiment, source_ids):
        query = """
            INSERT INTO insights (id, topic, trigger, frequency, sentiment, source_ids, created_at)
            VALUES (uuid(), %s, %s, %s, %s, %s, %s)
        """
        self.session.execute(query, (topic, trigger, frequency, sentiment, source_ids, datetime.now()))

