from bs4 import BeautifulSoup
from langchain_core.documents import Document
import json


def clean_text(value):
    if not value:
        return ""

    return BeautifulSoup(
        str(value),
        "html.parser"
    ).get_text("\n", strip=True)


def clean_value(value):
    if value is None:
        return ""

    return str(value).strip()


def clean_list(value):
    if not value:
        return ""

    if isinstance(value, list):
        return value if value else ""

    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return parsed if parsed else ""

        return parsed

    except (json.JSONDecodeError, TypeError):
        return str(value)


def create_document(scheme):

    content = f"""
Scheme Name:
{clean_value(scheme["name"])}

Description:
{clean_text(scheme["description"])}

Benefits:
{clean_text(scheme["benefits"])}

Eligibility:
{clean_text(scheme["eligibility_text"])}

Application Process:
{clean_text(scheme["application_process"])}

Documents Required:
{clean_text(scheme["documents_required"])}
""".strip()

    metadata = {
        "scheme_name": clean_value(scheme["name"]),

        "ministry": clean_value(
            scheme["ministry"]
        ),

        "department": clean_value(
            scheme["department"]
        ),

        "state": clean_value(
            scheme["state"]
        ),

        "category": clean_value(
            scheme["category"]
        ),

        "beneficiary_type": clean_value(
            scheme["beneficiary_type"]
        ),

        "official_url": clean_value(
            scheme["official_url"]
        ),

        "apply_url": clean_value(
            scheme["apply_url"]
        ),

        "eligibility_age_min": scheme[
            "eligibility_age_min"
        ],

        "eligibility_age_max": scheme[
            "eligibility_age_max"
        ],

        "eligibility_gender": clean_value(
            scheme["eligibility_gender"]
        ),

        "eligibility_caste": clean_list(
            scheme["eligibility_caste"]
        ),

        "eligibility_income_max": scheme[
            "eligibility_income_max"
        ],

        "eligibility_residence": clean_value(
            scheme["eligibility_residence"]
        ),

        "eligibility_state": clean_list(
            scheme["eligibility_state"]
        ),

        "eligibility_disability": scheme[
            "eligibility_disability"
        ],

        "eligibility_bpl": scheme[
            "eligibility_bpl"
        ],
    }

    return Document(
        page_content=content,
        metadata=metadata
    )