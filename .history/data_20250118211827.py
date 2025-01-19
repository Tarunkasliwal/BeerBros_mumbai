import csv

data = [
    {
        "id": "c56a4180-65aa-42ec-a945-5fd21dec0538",
        "source": "News Website",
        "title": "Sample Title",
        "content": "Sample content of the article goes here.",
        "url": "https://example.com",
        "timestamp": "2025-01-18 10:00:00"
    }
]

with open("scraped_data.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "source", "title", "content", "url", "timestamp"])
    writer.writeheader()
    writer.writerows(data)

print("CSV file created as scraped_data.csv")
