from flask import Flask, render_template, request, jsonify
import json
import requests
from config import (
    BASE_API_URL,
    LANGFLOW_ID,
    FLOW_ID,
    APPLICATION_TOKEN,
    ENDPOINT,
    TWEAKS
)

app = Flask(__name__, static_url_path='')

def run_flow(message, endpoint=ENDPOINT or FLOW_ID, output_type="chat", 
             input_type="chat", tweaks=TWEAKS, application_token=APPLICATION_TOKEN):
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"
    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = None
    if tweaks:
        payload["tweaks"] = tweaks
    if application_token:
        headers = {"Authorization": "Bearer " + application_token, "Content-Type": "application/json"}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_message():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'status': 'error', 'message': 'No message provided'}), 400

        message = data['message']
        response = run_flow(message)
        
        if isinstance(response, dict) and 'error' in response:
            return jsonify({'status': 'error', 'message': response['error']}), 500
            
        if 'messages' in response and response['messages']:
            message_content = response['messages'][0].get('message', '')
            return jsonify({'status': 'success', 'response': message_content})
        else:
            return jsonify({'status': 'error', 'message': 'No messages found in response'}), 500
            
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)