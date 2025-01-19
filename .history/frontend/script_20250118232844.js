const apiUrl = 'http://127.0.0.1:5000'; // Backend URL

document.getElementById('searchForm').addEventListener('submit', async function (event) {
    event.preventDefault();
    const query = document.getElementById('query').value;

    // Fetch search results
    const response = await fetch(`${apiUrl}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
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
            <p>Score: ${item.relevance_score}</p>
            <button onclick='saveResult(${JSON.stringify(item)})'>Save</button>
        `;
        resultsDiv.appendChild(div);
    });
}

async function saveResult(item) {
    const response = await fetch(`${apiUrl}/save`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(item)
    });

    const result = await response.json();
    alert(result.status || result.error);
}
