def analyse_product(description, location, website=""):
    """Portfolio-demo market analysis. No external API calls."""
    text = (description or "").lower()

    if "vet" in text or "animal" in text:
        name = "Veterinary workflow solution"
        segments = [
            "Independent veterinary practices",
            "Veterinary clinics",
            "Veterinary groups",
            "Animal hospitals",
            "Emergency veterinary clinics",
        ]
        roles = ["Practice Manager", "Clinical Director", "Practice Owner", "Veterinary Director"]
        terms = [
            "veterinary practice", "veterinary clinic", "animal hospital",
            "veterinary group", "emergency veterinary clinic", "independent veterinary practice"
        ]
        excludes = ["veterinary software", "veterinary recruitment", "veterinary pharmaceuticals"]
        problem = "Reducing administrative work around veterinary consultations and clinical documentation."
    elif "account" in text or "bookkeep" in text:
        name = "Accountancy service"
        segments = ["Small businesses", "Growing SMEs", "Professional services firms", "Retail businesses", "Startups"]
        roles = ["Founder", "Managing Director", "Finance Director", "Operations Director"]
        terms = ["small business", "professional services firm", "retail company", "startup", "consultancy", "agency"]
        excludes = ["accountancy software", "accountancy recruitment", "accounting training"]
        problem = "Helping organisations manage finance and reporting more efficiently."
    else:
        name = "Your product or service"
        segments = ["Small and medium businesses", "Professional services firms", "Growing companies", "Multi-site organisations", "Independent businesses"]
        roles = ["Founder", "Managing Director", "Operations Director", "Commercial Director"]
        terms = ["professional services", "business services", "independent business", "growing company", "agency", "consultancy"]
        excludes = ["recruitment", "software vendor"]
        problem = "Helping organisations improve a business process or customer outcome."

    return {
        "product_name": name,
        "simple_description": description.strip() or "Portfolio demo product/service.",
        "problem_solved": problem,
        "customer_segments": segments,
        "decision_makers": roles,
        "search_terms": terms,
        "exclude_terms": excludes,
        "market_reasoning": f"Demo strategy for {location}. This is sample portfolio data, not live market research.",
        "target_location": location,
    }
