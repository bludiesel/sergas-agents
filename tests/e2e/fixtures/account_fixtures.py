"""
Realistic account fixtures for E2E testing.

Generates 50+ realistic account records with varying characteristics:
- Healthy accounts
- At-risk accounts
- High-value accounts
- Churned accounts
- Growth accounts
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import random


class AccountFixtureGenerator:
    """Generate realistic account test data."""

    INDUSTRIES = [
        "Technology", "Healthcare", "Finance", "Manufacturing",
        "Retail", "Education", "Energy", "Telecommunications",
        "Media", "Transportation", "Real Estate", "Hospitality"
    ]

    ACCOUNT_TYPES = ["Customer", "Prospect", "Partner", "Competitor"]

    RATINGS = ["Hot", "Warm", "Cold"]

    COMPANY_NAMES = [
        "Tech Innovations Inc", "Global Healthcare Solutions", "FinTech Corp",
        "Advanced Manufacturing Ltd", "Retail Excellence Group", "EduTech Systems",
        "Green Energy Partners", "TeleCom Solutions", "Media Dynamics Inc",
        "Transport Logistics LLC", "Property Management Co", "Hospitality Services",
        "Data Analytics Corp", "Cloud Infrastructure Inc", "CyberSecurity Experts",
        "AI Research Labs", "Biotech Ventures", "Investment Holdings",
        "Precision Engineering", "E-Commerce Platform", "Learning Management Systems",
        "Renewable Energy Co", "Network Services Inc", "Broadcast Media Group",
        "Freight Solutions", "Commercial Real Estate", "Hotel Management Corp",
        "Business Intelligence Ltd", "SaaS Innovations", "Security Systems Inc",
        "Machine Learning Co", "Medical Devices Inc", "Wealth Management",
        "Industrial Automation", "Online Marketplace", "Virtual Learning Inc",
        "Solar Power Systems", "5G Networks Corp", "Streaming Services",
        "Supply Chain Solutions", "Property Development", "Resort Management",
        "Analytics Platform", "DevOps Tools Inc", "Risk Management Co",
        "Robotics Systems", "Pharmaceutical Research", "Private Equity Fund",
        "Manufacturing Tech", "Fashion Retail Group", "Educational Publishing"
    ]

    @classmethod
    def generate_healthy_accounts(cls, count: int = 15) -> List[Dict[str, Any]]:
        """Generate healthy, engaged accounts."""
        accounts = []
        base_date = datetime.now()

        for i in range(count):
            account_id = f"ACC_HEALTHY_{i:03d}"
            accounts.append({
                "id": account_id,
                "Account_Name": cls.COMPANY_NAMES[i],
                "Account_Number": f"ACN-{10000 + i}",
                "Account_Type": "Customer",
                "Industry": random.choice(cls.INDUSTRIES),
                "Rating": random.choice(["Hot", "Warm"]),
                "Annual_Revenue": random.randint(1000000, 50000000),
                "Number_of_Employees": random.randint(50, 5000),
                "Phone": f"+1-555-{random.randint(1000, 9999)}",
                "Website": f"https://www.{cls.COMPANY_NAMES[i].lower().replace(' ', '')}.com",

                # Health indicators
                "Last_Activity_Time": (base_date - timedelta(days=random.randint(1, 7))).isoformat(),
                "Open_Deals_Count": random.randint(2, 5),
                "Deal_Value": random.randint(100000, 1000000),
                "NPS_Score": random.randint(8, 10),
                "Support_Tickets_Count": random.randint(0, 2),
                "Product_Adoption_Score": random.randint(85, 100),
                "Engagement_Score": random.randint(80, 100),

                # Metadata
                "Created_Time": (base_date - timedelta(days=random.randint(365, 1095))).isoformat(),
                "Modified_Time": (base_date - timedelta(days=random.randint(1, 7))).isoformat(),
                "Owner": {
                    "id": f"owner_{i % 5 + 1}",
                    "name": f"Account Manager {i % 5 + 1}",
                    "email": f"manager{i % 5 + 1}@company.com"
                },

                # Contact info
                "Billing_Street": f"{random.randint(100, 9999)} Main St",
                "Billing_City": random.choice(["New York", "San Francisco", "Chicago", "Austin", "Boston"]),
                "Billing_State": random.choice(["NY", "CA", "IL", "TX", "MA"]),
                "Billing_Code": f"{random.randint(10000, 99999)}",
                "Billing_Country": "USA",

                "Description": f"Healthy customer account with strong engagement and growth potential.",
            })

        return accounts

    @classmethod
    def generate_at_risk_accounts(cls, count: int = 15) -> List[Dict[str, Any]]:
        """Generate at-risk accounts needing attention."""
        accounts = []
        base_date = datetime.now()

        for i in range(count):
            account_id = f"ACC_RISK_{i:03d}"
            accounts.append({
                "id": account_id,
                "Account_Name": cls.COMPANY_NAMES[15 + i],
                "Account_Number": f"ACN-{20000 + i}",
                "Account_Type": "Customer",
                "Industry": random.choice(cls.INDUSTRIES),
                "Rating": "Cold",
                "Annual_Revenue": random.randint(500000, 5000000),
                "Number_of_Employees": random.randint(25, 500),
                "Phone": f"+1-555-{random.randint(1000, 9999)}",
                "Website": f"https://www.{cls.COMPANY_NAMES[15 + i].lower().replace(' ', '')}.com",

                # Risk indicators
                "Last_Activity_Time": (base_date - timedelta(days=random.randint(60, 180))).isoformat(),
                "Open_Deals_Count": 0,
                "Deal_Value": 0,
                "NPS_Score": random.randint(1, 5),
                "Support_Tickets_Count": random.randint(5, 15),
                "Product_Adoption_Score": random.randint(20, 50),
                "Engagement_Score": random.randint(10, 40),
                "Churn_Risk_Score": random.randint(70, 95),

                # Metadata
                "Created_Time": (base_date - timedelta(days=random.randint(365, 730))).isoformat(),
                "Modified_Time": (base_date - timedelta(days=random.randint(60, 180))).isoformat(),
                "Owner": {
                    "id": f"owner_{i % 5 + 1}",
                    "name": f"Account Manager {i % 5 + 1}",
                    "email": f"manager{i % 5 + 1}@company.com"
                },

                "Billing_Street": f"{random.randint(100, 9999)} Commerce Blvd",
                "Billing_City": random.choice(["Seattle", "Denver", "Atlanta", "Phoenix", "Portland"]),
                "Billing_State": random.choice(["WA", "CO", "GA", "AZ", "OR"]),
                "Billing_Code": f"{random.randint(10000, 99999)}",
                "Billing_Country": "USA",

                "Description": f"At-risk account showing declining engagement and activity.",
            })

        return accounts

    @classmethod
    def generate_high_value_accounts(cls, count: int = 10) -> List[Dict[str, Any]]:
        """Generate high-value strategic accounts."""
        accounts = []
        base_date = datetime.now()

        for i in range(count):
            account_id = f"ACC_HIGHVAL_{i:03d}"
            accounts.append({
                "id": account_id,
                "Account_Name": cls.COMPANY_NAMES[30 + i],
                "Account_Number": f"ACN-{30000 + i}",
                "Account_Type": "Customer",
                "Industry": random.choice(cls.INDUSTRIES),
                "Rating": "Hot",
                "Annual_Revenue": random.randint(10000000, 100000000),
                "Number_of_Employees": random.randint(1000, 50000),
                "Phone": f"+1-555-{random.randint(1000, 9999)}",
                "Website": f"https://www.{cls.COMPANY_NAMES[30 + i].lower().replace(' ', '')}.com",

                # Strategic account indicators
                "Last_Activity_Time": (base_date - timedelta(days=random.randint(1, 3))).isoformat(),
                "Open_Deals_Count": random.randint(5, 10),
                "Deal_Value": random.randint(1000000, 10000000),
                "NPS_Score": random.randint(9, 10),
                "Support_Tickets_Count": random.randint(0, 1),
                "Product_Adoption_Score": random.randint(90, 100),
                "Engagement_Score": random.randint(95, 100),
                "Strategic_Account": True,
                "Executive_Sponsor": f"VP {i}",

                "Created_Time": (base_date - timedelta(days=random.randint(730, 1825))).isoformat(),
                "Modified_Time": (base_date - timedelta(days=random.randint(1, 3))).isoformat(),
                "Owner": {
                    "id": "owner_executive",
                    "name": "Executive Account Manager",
                    "email": "executive@company.com"
                },

                "Billing_Street": f"{random.randint(100, 9999)} Corporate Drive",
                "Billing_City": random.choice(["New York", "San Francisco", "Los Angeles"]),
                "Billing_State": random.choice(["NY", "CA"]),
                "Billing_Code": f"{random.randint(10000, 99999)}",
                "Billing_Country": "USA",

                "Description": f"Strategic high-value account requiring executive attention.",
            })

        return accounts

    @classmethod
    def generate_growth_accounts(cls, count: int = 10) -> List[Dict[str, Any]]:
        """Generate accounts with strong growth potential."""
        accounts = []
        base_date = datetime.now()

        for i in range(count):
            account_id = f"ACC_GROWTH_{i:03d}"
            accounts.append({
                "id": account_id,
                "Account_Name": cls.COMPANY_NAMES[40 + i],
                "Account_Number": f"ACN-{40000 + i}",
                "Account_Type": "Customer",
                "Industry": random.choice(cls.INDUSTRIES),
                "Rating": "Warm",
                "Annual_Revenue": random.randint(2000000, 20000000),
                "Number_of_Employees": random.randint(100, 2000),
                "Phone": f"+1-555-{random.randint(1000, 9999)}",
                "Website": f"https://www.{cls.COMPANY_NAMES[40 + i].lower().replace(' ', '')}.com",

                # Growth indicators
                "Last_Activity_Time": (base_date - timedelta(days=random.randint(1, 14))).isoformat(),
                "Open_Deals_Count": random.randint(2, 4),
                "Deal_Value": random.randint(200000, 2000000),
                "NPS_Score": random.randint(7, 9),
                "Support_Tickets_Count": random.randint(1, 3),
                "Product_Adoption_Score": random.randint(70, 90),
                "Engagement_Score": random.randint(70, 90),
                "Growth_Rate": random.randint(20, 50),
                "Expansion_Opportunity": True,

                "Created_Time": (base_date - timedelta(days=random.randint(180, 730))).isoformat(),
                "Modified_Time": (base_date - timedelta(days=random.randint(1, 14))).isoformat(),
                "Owner": {
                    "id": f"owner_{i % 5 + 1}",
                    "name": f"Account Manager {i % 5 + 1}",
                    "email": f"manager{i % 5 + 1}@company.com"
                },

                "Billing_Street": f"{random.randint(100, 9999)} Innovation Way",
                "Billing_City": random.choice(["Austin", "Seattle", "Boston", "San Diego"]),
                "Billing_State": random.choice(["TX", "WA", "MA", "CA"]),
                "Billing_Code": f"{random.randint(10000, 99999)}",
                "Billing_Country": "USA",

                "Description": f"Growing account with expansion opportunities.",
            })

        return accounts


def get_all_test_accounts() -> List[Dict[str, Any]]:
    """Get all test account fixtures (50 total)."""
    all_accounts = []
    all_accounts.extend(AccountFixtureGenerator.generate_healthy_accounts(15))
    all_accounts.extend(AccountFixtureGenerator.generate_at_risk_accounts(15))
    all_accounts.extend(AccountFixtureGenerator.generate_high_value_accounts(10))
    all_accounts.extend(AccountFixtureGenerator.generate_growth_accounts(10))
    return all_accounts


def get_accounts_by_owner(owner_id: str, all_accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter accounts by owner."""
    return [acc for acc in all_accounts if acc.get("Owner", {}).get("id") == owner_id]


def get_high_risk_accounts(all_accounts: List[Dict[str, Any]], risk_threshold: int = 70) -> List[Dict[str, Any]]:
    """Get accounts above risk threshold."""
    return [acc for acc in all_accounts if acc.get("Churn_Risk_Score", 0) >= risk_threshold]
