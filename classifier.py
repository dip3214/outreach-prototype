"""
Local, rule-based sector classification. Runs entirely on your machine —
no contact data is sent to any external API to get classified.

Edit SECTOR_KEYWORDS to tune this for your actual contact list.
"""

SECTOR_KEYWORDS = {
    "healthcare": ["health", "clinic", "hospital", "medi", "pharma", "diagnostic", "care"],
    "fintech": ["fin", "bank", "capital", "invest", "pay", "wealth", "insur", "credit"],
    "saas_tech": ["tech", "software", "labs", "ai", "cloud", "data", "digital", "app"],
    "manufacturing": ["manufactur", "industries", "engineering", "steel", "auto", "textile"],
    "retail_ecom": ["retail", "commerce", "store", "mart", "fashion", "shop"],
}

DEFAULT_SECTOR = "general"


def classify(company_name: str) -> str:
    if not company_name:
        return DEFAULT_SECTOR
    name = company_name.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return sector
    return DEFAULT_SECTOR
