// script.js
document.getElementById('searchForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const query = document.getElementById('query').value;

    const response = await fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
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
        div.innerHTML = `
            <h3>${item.title}</h3>
            <p>Relevance Score: ${item.relevance_score}</p>
            <button onclick="saveResult(${JSON.stringify(item)})">Save</button>
        `;
        resultsDiv.appendChild(div);
    });
}

async function saveResult(item) {
    const response = await fetch('/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify([item]),
    });

    const result = await response.json();
    alert(result.status);
}

document.getElementById('fetchData').addEventListener('click', async function() {
    const response = await fetch('/fetch', { method: 'GET' });
    const data = await response.json();

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'result-item';
        div.innerHTML = `<h3>${item.title}</h3><p>Relevance Score: ${item.score}</p>`;
        resultsDiv.appendChild(div);
    });
});
