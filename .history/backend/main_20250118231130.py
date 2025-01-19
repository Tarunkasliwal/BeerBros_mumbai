# main.py
from flask import Flask, request, jsonify
from utils import fetch_tavilia_data, get_cassandra_session, save_to_astra, fetch_all_from_astra

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    """Fetch data from Tavily API."""
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        tavily_data = fetch_tavilia_data(query)
        results = [{'title': item['title'], 'relevance_score': item['relevance_score']} for item in tavily_data['results']]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    """Save data to Astra DB."""
    data = request.json  # Expects a list of items [{'title': ..., 'relevance_score': ...}, ...]
    session = get_cassandra_session()
    save_to_astra(session, data)
    session.shutdown()
    return jsonify({'status': 'success'})

@app.route('/fetch', methods=['GET'])
def fetch():
    """Fetch data from Astra DB."""
    session = get_cassandra_session()
    data = fetch_all_from_astra(session)
    session.shutdown()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
