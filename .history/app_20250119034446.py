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

app = Flask(__name__)

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
    
    response = requests.post(api_url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to get a valid response. Status Code: {response.status_code}")
    
    return response.json()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_message():
    try:
        data = request.json
        message = data.get('message', '')
        
        response = run_flow(message)
        
        if 'messages' in response and response['messages']:
            message_content = response['messages'][0].get('message', '')
            return jsonify({'status': 'success', 'response': message_content})
        else:
            return jsonify({'status': 'error', 'message': 'No messages found in response'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)