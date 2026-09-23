_DEMO_COMPANIES = [
    ("Greenfield Veterinary Practice Ltd", "DEMO0001", "London", "veterinary practice", 94),
    ("Riverside Animal Care Ltd", "DEMO0002", "Manchester", "veterinary clinic", 91),
    ("Oakwood Veterinary Group Ltd", "DEMO0003", "Birmingham", "veterinary group", 89),
    ("Northgate Animal Hospital Ltd", "DEMO0004", "Leeds", "animal hospital", 87),
    ("Meadow Veterinary Services Ltd", "DEMO0005", "Bristol", "veterinary practice", 85),
    ("City Pet Care Group Ltd", "DEMO0006", "London", "veterinary clinic", 83),
    ("Parkside Veterinary Centre Ltd", "DEMO0007", "Nottingham", "veterinary practice", 81),
    ("Harbour Animal Health Ltd", "DEMO0008", "Liverpool", "animal hospital", 79),
    ("Westfield Veterinary Group Ltd", "DEMO0009", "Reading", "veterinary group", 77),
    ("Central Veterinary Care Ltd", "DEMO0010", "Cambridge", "veterinary clinic", 75),
    ("Beacon Professional Services Ltd", "DEMO0011", "London", "professional services", 73),
    ("Northstar Business Solutions Ltd", "DEMO0012", "Birmingham", "business services", 71),
]

def discover_market(search_terms, results_per_term=30, exclude_terms=None, active_only=True):
    """Portfolio-demo discovery. Returns fictional sample organisations only."""
    terms = list(search_terms or [])
    results = []
    for i, (name, number, city, matched, score) in enumerate(_DEMO_COMPANIES):
        results.append({
            "name": name,
            "company_number": number,
            "status": "active",
            "company_status": "active",
            "company_type": "ltd",
            "address": f"{10+i} Demo Street, {city}, United Kingdom",
            "date_created": "2020-01-01",
            "matched_search_term": terms[i % len(terms)] if terms else matched,
            "source": "Portfolio demo data",
            "reach_status": "Discovered",
            "relevance_score": score,
            "website": "",
            "email": "",
            "phone": "",
            "contact_page": "",
            "contact_status": "Demo only",
        })
    return results
