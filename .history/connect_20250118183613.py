import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Load secure connect bundle
secure_connect_bundle = 'path/to/your/secure-connect-bundle.zip'
cloud_config= {
    'secure_connect_bundle': secure_connect_bundle
}

# Authentication details
auth_provider = PlainTextAuthProvider(
    username='your_username', 
    password='your_password'
)

cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()