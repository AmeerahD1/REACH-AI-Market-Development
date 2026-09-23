def hunter_is_configured():
    # Keep the existing UI enabled in portfolio mode without a Hunter key.
    return True

def find_people_for_company(company_name, limit=10):
    company = company_name or "Demo Organisation"
    people = [
        {
            "name": "Alex Morgan (Demo)",
            "first_name": "Alex",
            "last_name": "Morgan",
            "job_title": "Practice Manager",
            "seniority": "manager",
            "department": "operations",
            "email": "alex.morgan@example.com",
            "email_type": "demo",
            "confidence": 95,
            "verification_status": "demo",
            "company": company,
            "domain": "example.com",
            "phone": "—",
            "linkedin": "—",
            "source": "Portfolio demo data",
        },
        {
            "name": "Jordan Taylor (Demo)",
            "first_name": "Jordan",
            "last_name": "Taylor",
            "job_title": "Clinical Director",
            "seniority": "executive",
            "department": "clinical",
            "email": "jordan.taylor@example.com",
            "email_type": "demo",
            "confidence": 92,
            "verification_status": "demo",
            "company": company,
            "domain": "example.com",
            "phone": "—",
            "linkedin": "—",
            "source": "Portfolio demo data",
        },
    ]
    return people[:max(1, min(int(limit), len(people)))], None

def find_people_for_companies(companies, max_companies=5, per_company=10):
    all_people = []
    for company in (companies or [])[:max_companies]:
        name = company.get("name") if isinstance(company, dict) else str(company)
        people, _ = find_people_for_company(name, per_company)
        all_people.extend(people)
    return all_people, []
