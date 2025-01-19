from dotenv import load_dotenv
import os

load_dotenv()

ASTRA_DB_SECURE_BUNDLE_PATH = os.getenv('ASTRA_DB_SECURE_BUNDLE_PATH')
ASTRA_DB_CLIENT_ID = os.getenv('ASTRA_DB_CLIENT_ID')
ASTRA_DB_CLIENT_SECRET = os.getenv('ASTRA_DB_CLIENT_SECRET')
ASTRA_DB_KEYSPACE = os.getenv('ASTRA_DB_KEYSPACE')