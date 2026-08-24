# app/rag/query_parser.py

import re


# =========================================================
# Indian States / Union Territories
# =========================================================

INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Puducherry",
    "Chandigarh",
]


# =========================================================
# Category keywords
# =========================================================
#
# These category names should match the category values
# stored in the scheme dataset.
# =========================================================

CATEGORY_KEYWORDS = {

    # -----------------------------------------------------
    # Agriculture
    # -----------------------------------------------------

    "Agriculture,Rural & Environment": [
        "farmer",
        "farmers",
        "farming",
        "agriculture",
        "agricultural",
        "agriculturist",
        "crop",
        "crops",
        "cultivation",
        "cultivator",
        "fisherman",
        "fishermen",
        "fisher",
        "fisheries",
        "fishing",
        "fish farming",
        "livestock",
        "cattle",
        "dairy",
        "goat",
        "sheep",
        "poultry",
        "animal husbandry",
        "rural",
        "rural development",
    ],


    # -----------------------------------------------------
    # Education
    # -----------------------------------------------------

    "Education & Learning": [
        "student",
        "students",
        "education",
        "educational",
        "school",
        "schools",
        "college",
        "colleges",
        "university",
        "universities",
        "scholarship",
        "scholarships",
        "study",
        "studies",
        "learning",
        "academic",
        "academics",
        "tuition",
        "school fees",
        "college fees",
    ],


    # -----------------------------------------------------
    # Jobs
    # -----------------------------------------------------

    "Jobs": [
        "job",
        "jobs",
        "employment",
        "employed",
        "unemployed",
        "worker",
        "workers",
        "workforce",
        "career",
        "careers",
        "occupation",
        "vocational",
        "skill",
        "skills",
        "training",
        "internship",
        "internships",
        "placement",
        "placements",
    ],


    # -----------------------------------------------------
    # Business
    # -----------------------------------------------------

    "Business & Self-employed": [
        "business",
        "businesses",
        "entrepreneur",
        "entrepreneurs",
        "entrepreneurship",
        "startup",
        "startups",
        "enterprise",
        "enterprises",
        "self employed",
        "self-employed",
        "self employment",
        "self-employment",
        "small business",
        "micro business",
        "msme",
        "shop",
        "shopkeeper",
        "trader",
        "trading",
        "vendor",
        "vendors",
        "commercial",
    ],


    # -----------------------------------------------------
    # Health
    # -----------------------------------------------------

    "Health & Wellness": [
        "health",
        "healthcare",
        "health care",
        "medical",
        "medicine",
        "medicines",
        "hospital",
        "hospitals",
        "doctor",
        "doctors",
        "treatment",
        "treatments",
        "disease",
        "diseases",
        "illness",
        "illnesses",
        "surgery",
        "surgical",
        "diagnosis",
        "diagnostic",
        "health insurance",
        "medical assistance",
        "medical treatment",
    ],


    # -----------------------------------------------------
    # Housing / Local Services
    # -----------------------------------------------------

    "Housing & Local services": [
        "house",
        "houses",
        "housing",
        "home",
        "homes",
        "rent",
        "rental",
        "shelter",
        "residence",
        "residential",
        "accommodation",
        "sanitation",
        "toilet",
        "water",
        "drinking water",
        "local service",
        "local services",
    ],


    # -----------------------------------------------------
    # Women and Child
    # -----------------------------------------------------

    "Women and Child": [
        "woman",
        "women",
        "female",
        "girl",
        "girls",
        "lady",
        "ladies",
        "mother",
        "mothers",
        "pregnant",
        "pregnancy",
        "maternity",
        "child",
        "children",
        "childcare",
        "baby",
        "infant",
        "daughter",
    ],


    # -----------------------------------------------------
    # Social Welfare
    # -----------------------------------------------------

    "Social welfare & Empowerment": [
        "social welfare",
        "social security",
        "social assistance",
        "pension",
        "senior citizen",
        "senior citizens",
        "elderly",
        "old age",
        "disability",
        "disabled",
        "person with disability",
        "persons with disabilities",
        "widow",
        "widows",
        "destitute",
        "scheduled caste",
        "sc category",
        "scheduled tribe",
        "st category",
        "minority",
        "minorities",
        "backward class",
        "financial assistance",
    ],
}


# =========================================================
# Normalize query
# =========================================================

def normalize_query(query):
    """
    Normalize the query before performing keyword matching.

    This function is used only by the parser.
    The original query is still passed to semantic search.
    """

    if not query:
        return ""

    return " ".join(
        query.lower().strip().split()
    )


# =========================================================
# Find State
# =========================================================

def find_state(query):
    """
    Find an Indian state or Union Territory in the query.

    Returns:
        Exact state name from INDIAN_STATES
        or None if no state is detected.
    """

    query_lower = normalize_query(query)

    if not query_lower:
        return None

    # Longer names first to avoid partial matches.
    # e.g. "Jammu and Kashmir" before "Kashmir"
    states_sorted = sorted(
        INDIAN_STATES,
        key=len,
        reverse=True,
    )

    for state in states_sorted:

        if state.lower() in query_lower:
            return state

    return None


# =========================================================
# Find Category
# =========================================================

def find_category(query):
    """
    Find the most relevant category in the query.

    Returns:
        Category name or None.
    """

    query_lower = normalize_query(query)

    if not query_lower:
        return None

    for category, keywords in CATEGORY_KEYWORDS.items():

        # Check longer phrases first.
        # e.g. "health care" before "health"
        keywords_sorted = sorted(
            keywords,
            key=len,
            reverse=True,
        )

        for keyword in keywords_sorted:

            if keyword.lower() in query_lower:
                return category

    return None


# =========================================================
# Find Age
# =========================================================

def find_age(query):
    """
    Extract age from natural language.

    Examples:
        "I am 35 years old"  -> 35
        "25yr old woman"     -> 25
        "45-year-old man"    -> 45

    Returns:
        int or None
    """

    match = re.search(
        r"\b(\d{1,3})\s*[-\s]?(?:year|yr)s?[-\s]?(?:old)?\b",
        query,
        re.IGNORECASE,
    )

    if match:
        age = int(match.group(1))
        # Sanity check: valid human age range
        if 0 < age < 120:
            return age

    return None


# =========================================================
# Find Gender
# =========================================================

_GENDER_ALIASES = {
    "male": "male",
    "man": "male",
    "boy": "male",
    "husband": "male",
    "father": "male",
    "female": "female",
    "woman": "female",
    "girl": "female",
    "wife": "female",
    "mother": "female",
    "lady": "female",
}

def find_gender(query):
    """
    Detect gender from natural language.

    Returns:
        "male", "female", or None
    """

    query_lower = normalize_query(query)

    # Check longer aliases first to avoid partial matches
    aliases_sorted = sorted(
        _GENDER_ALIASES.keys(),
        key=len,
        reverse=True,
    )

    for alias in aliases_sorted:
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, query_lower):
            return _GENDER_ALIASES[alias]

    return None


# =========================================================
# Find Income
# =========================================================

def find_income(query):
    """
    Extract annual income in rupees from natural language.

    Supports:
        "under ₹2 lakh"       -> 200000.0
        "below rs 5 lakh"     -> 500000.0
        "income upto 3 lac"   -> 300000.0
        "earning 2.5 lakh"    -> 250000.0

    Returns:
        float (in rupees) or None
    """

    match = re.search(
        r"(?:under|below|upto|up\s+to|less\s+than|earning|income)?\s*"
        r"(?:rs\.?|₹|inr)?\s*"
        r"(\d[\d,]*(?:\.\d+)?)\s*"
        r"(?:lakh|lac|l)\b",
        query,
        re.IGNORECASE,
    )

    if match:
        raw = match.group(1).replace(",", "")
        try:
            return float(raw) * 100_000
        except ValueError:
            return None

    return None


# =========================================================
# Parse Query
# =========================================================

def parse_query(query):
    """
    Parse one natural-language government-scheme query.

    Example:

        Input:
            I am a 35 year old male farmer from Haryana
            earning under ₹2 lakh

        Output:
            {
                "state":    "Haryana",
                "category": "Agriculture,Rural & Environment",
                "age":      35,
                "gender":   "male",
                "income":   200000.0
            }
    """

    if not isinstance(query, str):
        return {
            "state": None,
            "category": None,
            "age": None,
            "gender": None,
            "income": None,
        }

    query = query.strip()

    if not query:
        return {
            "state": None,
            "category": None,
            "age": None,
            "gender": None,
            "income": None,
        }

    return {
        "state":    find_state(query),
        "category": find_category(query),
        "age":      find_age(query),
        "gender":   find_gender(query),
        "income":   find_income(query),
    }


# =========================================================
# Local single-query test
# =========================================================
#
# Run with:  python -m app.rag.query_parser
#
if __name__ == "__main__":

    query = input("\nEnter query:\n").strip()
    parsed = parse_query(query)
    print("\nParsed query:")
    print(parsed)