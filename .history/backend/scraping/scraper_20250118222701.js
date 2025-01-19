const puppeteer = require('puppeteer');
const cassandra = require('cassandra-driver');

const client = new cassandra.Client({
  cloud: { secureConnectBundle: 'C:\\path\\to\\secure-connect-bundle.zip' },
  credentials: { username: 'YOUR_USERNAME', password: 'YOUR_PASSWORD' }
});

async function scrapeData(topic) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(`https://www.google.com/search?q=${encodeURIComponent(topic)}`, { waitUntil: 'networkidle2' });

  const data = await page.evaluate(() => {
    const elements = document.querySelectorAll('.tF2Cxc');
    return Array.from(elements, element => ({
      title: element.querySelector('.DKV0Md').innerText,
      link: element.querySelector('a').href,
      snippet: element.querySelector('.IsZvec').innerText
    }));
  });

  await browser.close();

  // Save data to Astra DB
  const query = 'INSERT INTO your_keyspace.your_table (id, title, link, snippet) VALUES (?, ?, ?, ?)';
  data.forEach(item => {
    client.execute(query, [cassandra.types.uuid(), item.title, item.link, item.snippet], { prepare: true });
  });

  return JSON.stringify(data);
}

module.exports = { scrapeData };