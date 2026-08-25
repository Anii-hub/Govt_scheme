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


def sanitize_metadata(meta: dict) -> dict:
    sanitized = {}
    for k, v in meta.items():
        if v is None:
            sanitized[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            sanitized[k] = v
        elif isinstance(v, list):
            sanitized[k] = ", ".join(str(x) for x in v if x)
        else:
            sanitized[k] = str(v)
    return sanitized


def create_document(scheme):

    content = f"""
Scheme Name:
{clean_value(scheme.get("name"))}

Description:
{clean_text(scheme.get("description"))}

Benefits:
{clean_text(scheme.get("benefits"))}

Eligibility:
{clean_text(scheme.get("eligibility_text"))}

Application Process:
{clean_text(scheme.get("application_process"))}

Documents Required:
{clean_text(scheme.get("documents_required"))}
""".strip()

    metadata = {
        "scheme_name": clean_value(scheme.get("name")),
        "ministry": clean_value(scheme.get("ministry")),
        "department": clean_value(scheme.get("department")),
        "state": clean_value(scheme.get("state")),
        "category": clean_value(scheme.get("category")),
        "beneficiary_type": clean_value(scheme.get("beneficiary_type")),
        "official_url": clean_value(scheme.get("official_url")),
        "apply_url": clean_value(scheme.get("apply_url")),
        "eligibility_age_min": scheme.get("eligibility_age_min") if isinstance(scheme.get("eligibility_age_min"), (int, float)) else 0,
        "eligibility_age_max": scheme.get("eligibility_age_max") if isinstance(scheme.get("eligibility_age_max"), (int, float)) else 150,
        "eligibility_gender": clean_value(scheme.get("eligibility_gender")),
        "eligibility_caste": clean_value(clean_list(scheme.get("eligibility_caste"))),
        "eligibility_income_max": scheme.get("eligibility_income_max") if isinstance(scheme.get("eligibility_income_max"), (int, float)) else 0,
        "eligibility_residence": clean_value(scheme.get("eligibility_residence")),
        "eligibility_state": clean_value(clean_list(scheme.get("eligibility_state"))),
        "eligibility_disability": clean_value(scheme.get("eligibility_disability")),
        "eligibility_bpl": clean_value(scheme.get("eligibility_bpl")),
    }

    return Document(
        page_content=content,
        metadata=sanitize_metadata(metadata)
    )