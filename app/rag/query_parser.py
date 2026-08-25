# app/rag/query_parser.py


# =========================================================
# Indian States / Union Territories
# =========================================================

# app/rag/query_parser.py


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

    # Longer names first.
    #
    # Example:
    # "Jammu and Kashmir" should be matched as a complete
    # state name rather than accidentally matching another
    # shorter string first.
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
        #
        # Example:
        # "health care" should be checked before "health".
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
# Parse Query
# =========================================================

def parse_query(query):
    """
    Parse one natural-language government-scheme query.

    Example:

        Input:
            I am a farmer from Haryana looking for assistance

        Output:
            {
                "state": "Haryana",
                "category": "Agriculture,Rural & Environment"
            }

    Another example:

        Input:
            I am a 25 year old woman from Maharashtra

        Output:
            {
                "state": "Maharashtra",
                "category": "Women and Child"
            }
    """

    if not isinstance(query, str):

        return {
            "state": None,
            "category": None,
        }

    query = query.strip()

    if not query:

        return {
            "state": None,
            "category": None,
        }

    state = find_state(
        query
    )

    category = find_category(
        query
    )

    return {
        "state": state,
        "category": category,
    }


# =========================================================
# Local single-query test
# =========================================================
#
# This is NOT a multiple-query system.
#
# If you want to test this file directly:
#
#     python -m app.rag.query_parser
#
# It accepts ONE query and exits.
# =========================================================

if __name__ == "__main__":

    query = input(
        "\nEnter query:\n"
    ).strip()

    parsed = parse_query(
        query
    )

    print(
        "\nParsed query:"
    )

    print(
        parsed
    )