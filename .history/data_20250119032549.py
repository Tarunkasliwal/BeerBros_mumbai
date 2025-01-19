import requests
import json
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize SQLAlchemy
Base = declarative_base()

# Define the database model
class CompanyData(Base):
    __tablename__ = 'company_data'
    id = Column(Integer, primary_key=True)
    company_name = Column(String)
    search_date = Column(DateTime)
    domain = Column(String)
    industry = Column(String)
    competitors = Column(String)
    current_trends = Column(String)
    revenue_range = Column(String)
    employee_count = Column(String)
    founded_year = Column(String)
    hq_location = Column(String)
    social_media_presence = Column(String)
    growth_indicators = Column(String)
    market_position = Column(String)
    future_opportunities = Column(String)
    potential_risks = Column(String)
    last_updated = Column(DateTime)

# Set up the database connection (assuming PostgreSQL or any SQL database)
DATABASE_URL = 'postgresql://username:password@localhost/dbname'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

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
    
    def save_to_db(self, company_info):
        try:
            # Create a new CompanyData entry
            company_data = CompanyData(**company_info)
            
            # Add to the session and commit
            session.add(company_data)
            session.commit()
            print("Data successfully saved to database")
            return True
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False


def main():
    # Initialize with your API key
    API_KEY = "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"
    analyzer = CompanyAnalyzer(API_KEY)
    
    while True:
        company_name = input("Enter company name (or 'quit' to exit): ")
        if company_name.lower() == 'quit':
            break
            
        # Analyze company and save to PDF and Database
        company_info = analyzer.analyze_company(company_name)
        if company_info:
            analyzer.save_to_pdf(company_info)
            analyzer.save_to_db(company_info)
        else:
            print(f"Could not analyze company: {company_name}")

if __name__ == "__main__":
    main()
