// script.js
document.getElementById('searchForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const subreddit = document.getElementById('subreddit').value;
    const query = document.getElementById('query').value;
    
    const response = await fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ subreddit, query })
    });
    
    const data = await response.json();
    displayResults(data);
});

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    
    data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'result-item';
        div.innerHTML = `<h3>${item.title}</h3><p>Score: ${item.score || item.relevance_score}</p>`;
        resultsDiv.appendChild(div);
    });
}