const express = require('express');
const router = express.Router();
const scraper = require('../scraping/scraper');
const { exec } = require('child_process');

router.post('/submit-topic', async (req, res) => {
  const topic = req.body.topic;
  try {
    const scrapedData = await scraper.scrapeData(topic);
    exec(`python ../analysis/analyzer.py "${scrapedData}"`, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error executing Python script: ${error.message}`);
        return res.status(500).send('Error processing data');
      }
      const insights = JSON.parse(stdout);
      res.json(insights);
    });
  } catch (error) {
    console.error(`Error scraping data: ${error.message}`);
    res.status(500).send('Error scraping data');
  }
});

module.exports = router;