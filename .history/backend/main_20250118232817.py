from flask import Flask, request, jsonify
from flask_cors import CORS
from utils import fetch_tavilia_data, get_cassandra_session, save_to_astra

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    
    try:
        tavilia_data = fetch_tavilia_data(query)
        return jsonify(tavilia_data['results'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    session = get_cassandra_session()
    try:
        save_to_astra(session, [data])
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.shutdown()

if __name__ == '__main__':
    app.run(debug=True)
