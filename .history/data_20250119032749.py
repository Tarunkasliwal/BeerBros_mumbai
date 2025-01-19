import requests
import json
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement

class CompanyAnalyzer:
    def __init__(self, api_key, astra_client_id, astra_client_secret, astra_db_keyspace):
        self.api_key = api_key
        self.base_url = "https://api.tavilia.com/v1"  # Hypothetical API endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Connect to AstraDB
        secure_connect_bundle = 'D:\Beerbros_final_mumbai\secure-connect-beerbros-art.zip'  # Path to your secure connect bundle
        auth_provider = PlainTextAuthProvider(astra_client_id, astra_client_secret)
        cluster = Cluster(cloud={'secure_connect_bundle': secure_connect_bundle}, auth_provider=auth_provider)
        self.session = cluster.connect(astra_db_keyspace)
    
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
        
        # Structure the data for PDF and Database
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
            "social_media_presence": str(data.get("social_media", {})),
            "growth_indicators": data.get("growth_indicators", ""),
            "market_position": data.get("market_position", ""),
            "future_opportunities": data.get("opportunities", ""),
            "potential_risks": data.get("risks", ""),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return company_info

    def save_to_pdf(self, company_info, filename="company_analysis.pdf"):
        try:
            c = canvas.Canvas(filename, pagesize=letter)
            c.setFont("Helvetica", 10)
            width, height = letter
            
            y_position = height - 40
            for key, value in company_info.items():
                c.drawString(40, y_position, f"{key}: {value}")
                y_position -= 20
            
            c.save()
            print(f"Data successfully saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving to PDF: {e}")
            return False
    
    def save_to_astradb(self, company_info):
        try:
            # Define CQL insert statement
            query = """
                INSERT INTO company_data (company_name, search_date, domain, industry, competitors, 
                current_trends, revenue_range, employee_count, founded_year, hq_location, 
                social_media_presence, growth_indicators, market_position, future_opportunities, 
                potential_risks, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            
            # Prepare the statement
            statement = SimpleStatement(query)
            
            # Execute insert operation
            self.session.execute(statement, (
                company_info["company_name"],
                company_info["search_date"],
                company_info["domain"],
                company_info["industry"],
                company_info["competitors"],
                company_info["current_trends"],
                company_info["revenue_range"],
                company_info["employee_count"],
                company_info["founded_year"],
                company_info["hq_location"],
                company_info["social_media_presence"],
                company_info["growth_indicators"],
                company_info["market_position"],
                company_info["future_opportunities"],
                company_info["potential_risks"],
                company_info["last_updated"]
            ))

            print("Data successfully saved to AstraDB")
            return True
        except Exception as e:
            print(f"Error saving to AstraDB: {e}")
            return False


def main():
    # Initialize with your API key and AstraDB credentials
    API_KEY = "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"
    ASTRA_CLIENT_ID = "your_astra_client_id"
    ASTRA_CLIENT_SECRET = "your_astra_client_secret"
    ASTRA_DB_KEYSPACE = "your_keyspace_name"
    
    analyzer = CompanyAnalyzer(API_KEY, ASTRA_CLIENT_ID, ASTRA_CLIENT_SECRET, ASTRA_DB_KEYSPACE)
    
    while True:
        company_name = input("Enter company name (or 'quit' to exit): ")
        if company_name.lower() == 'quit':
            break
            
        # Analyze company and save to PDF and AstraDB
        company_info = analyzer.analyze_company(company_name)
        if company_info:
            analyzer.save_to_pdf(company_info)
            analyzer.save_to_astradb(company_info)
        else:
            print(f"Could not analyze company: {company_name}")

if __name__ == "__main__":
    main()
