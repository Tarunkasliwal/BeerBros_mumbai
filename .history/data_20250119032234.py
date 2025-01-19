import requests
import pandas as pd
import json
from datetime import datetime
import os

class CompanyAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.tavilia.com/v1"  # Note: This is a hypothetical API endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search_company(self, company_name):
        try:
            # Simulated API endpoint for company search
            endpoint = f"{self.base_url}/companies/search"
            params = {"query": company_name}
            
            # Make API request
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching company: {e}")
            return None
    
    def analyze_company(self, company_name):
        # Search company data
        data = self.search_company(company_name)
        if not data:
            return None
        
        # Structure the data for CSV
        company_info = {
            "company_name": company_name,
            "search_date": datetime.now().strftime("%Y-%m-%d"),
            "domain": data.get("domain", ""),
            "industry": data.get("industry", ""),
            "competitors": ", ".join(data.get("competitors", [])),
            "current_trends": ", ".join(data.get("trends", [])),
            "revenue_range": data.get("revenue_range", ""),
            "employee_count": data.get("employee_count", ""),
            "founded_year": data.get("founded_year", ""),
            "hq_location": data.get("headquarters", ""),
            "social_media_presence": data.get("social_media", {}),
            "growth_indicators": data.get("growth_indicators", ""),
            "market_position": data.get("market_position", ""),
            "future_opportunities": data.get("opportunities", ""),
            "potential_risks": data.get("risks", ""),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return company_info

    def save_to_csv(self, company_info, filename="company_analysis.csv"):
        try:
            # Convert to DataFrame
            df = pd.DataFrame([company_info])
            
            # Check if file exists
            file_exists = os.path.isfile(filename)
            
            # Save to CSV
            df.to_csv(filename, mode='a' if file_exists else 'w',
                     header=not file_exists, index=False)
            
            print(f"Data successfully saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return False

def main():
    # Initialize with your API key
    API_KEY = "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"
    analyzer = CompanyAnalyzer(API_KEY)
    
    while True:
        company_name = input("Enter company name (or 'quit' to exit): ")
        if company_name.lower() == 'quit':
            break
            
        # Analyze company and save to CSV
        company_info = analyzer.analyze_company(company_name)
        if company_info:
            analyzer.save_to_csv(company_info)
        else:
            print(f"Could not analyze company: {company_name}")

if __name__ == "__main__":
    main()