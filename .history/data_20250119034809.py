import requests

# Test URL
url = "https://api.langflow.astra.datastax.com/health"
response = requests.get(url)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")