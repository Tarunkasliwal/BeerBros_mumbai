# main.py
from flask import Flask, request, jsonify
from utils import fetch_reddit_data, fetch_tavilia_data
import pandas as pd

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    subreddit = data.get('subreddit')
    query = data.get('query')
    
    reddit_data = fetch_reddit_data(subreddit)
    tavilia_data = fetch_tavilia_data(query)
    
    # Process and combine data
    reddit_posts = [post['data'] for post in reddit_data['data']['children']]
    tavilia_results = tavilia_data['results']
    
    # Example processing: Extract titles and scores
    reddit_df = pd.DataFrame(reddit_posts)[['title', 'score']]
    tavilia_df = pd.DataFrame(tavilia_results)[['title', 'relevance_score']]
    
    combined_df = pd.concat([reddit_df, tavilia_df], axis=0)
    
    return jsonify(combined_df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)