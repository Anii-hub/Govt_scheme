import json
import os

from groq import Groq

import app.config


MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


# =========================================================
# Groq client
# =========================================================

def get_groq_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Please add your Groq API key to the environment."
        )

    return Groq(api_key=api_key)


# =========================================================
# Text limiter
# =========================================================

def limit_text(value, max_chars=3000):

    if value is None:
        return ""

    value = str(value).strip()

    if len(value) <= max_chars:
        return value

    return value[:max_chars] + "\n[Content truncated]"


# =========================================================
# Build context
# =========================================================

def build_context(results):

    context_parts = []

    for index, result in enumerate(results, start=1):

        document = result["document"]
        metadata = document.metadata

        scheme_name = metadata.get(
            "scheme_name",
            "Unknown scheme",
        )

        state = metadata.get(
            "state",
            "",
        )

        category = metadata.get(
            "category",
            "",
        )

        official_url = metadata.get(
            "official_url",
            "",
        )

        apply_url = metadata.get(
            "apply_url",
            "",
        )

        content = document.page_content

        # -------------------------------------------------
        # Limit content sent to Groq
        # -------------------------------------------------

        content = limit_text(
            content,
            max_chars=3000,
        )

        scheme_context = f"""
SCHEME {index}

Scheme Name:
{scheme_name}

State:
{state}

Category:
{category}

Official URL:
{official_url}

Application URL:
{apply_url}

Scheme Details:
{content}
""".strip()

        context_parts.append(
            scheme_context
        )

    return (
        "\n\n"
        + ("\n\n" + "=" * 60 + "\n\n").join(
            context_parts
        )
    )


# =========================================================
# Clean Groq response
# =========================================================

def clean_json_response(raw_answer):

    if not raw_answer:
        raise ValueError(
            "Groq returned an empty response."
        )

    raw_answer = raw_answer.strip()

    # -----------------------------------------------------
    # Remove markdown fences
    # -----------------------------------------------------

    if raw_answer.startswith("```json"):

        raw_answer = raw_answer[
            len("```json"):
        ].strip()

    elif raw_answer.startswith("```"):

        raw_answer = raw_answer[
            len("```"):
        ].strip()

    if raw_answer.endswith("```"):

        raw_answer = raw_answer[
            :-len("```")
        ].strip()

    return raw_answer


# =========================================================
# Validate answer
# =========================================================

def validate_answer(answer):

    if not isinstance(answer, dict):

        raise ValueError(
            "Groq response is not a JSON object."
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    if "summary" not in answer:

        answer["summary"] = ""

    if not isinstance(
        answer["summary"],
        str,
    ):

        answer["summary"] = str(
            answer["summary"]
        )

    # -----------------------------------------------------
    # Schemes
    # -----------------------------------------------------

    if "schemes" not in answer:

        answer["schemes"] = []

    if not isinstance(
        answer["schemes"],
        list,
    ):

        answer["schemes"] = []

    # -----------------------------------------------------
    # Maximum 3 schemes
    # -----------------------------------------------------

    answer["schemes"] = answer[
        "schemes"
    ][:3]

    # -----------------------------------------------------
    # Important note
    # -----------------------------------------------------

    if "important_note" not in answer:

        answer["important_note"] = (
            "Final eligibility is determined "
            "by the relevant government authority."
        )

    # -----------------------------------------------------
    # Validate individual schemes
    # -----------------------------------------------------

    for scheme in answer["schemes"]:

        if not isinstance(
            scheme,
            dict,
        ):
            continue

        if "scheme_name" not in scheme:
            scheme["scheme_name"] = ""

        if "state" not in scheme:
            scheme["state"] = ""

        if "category" not in scheme:
            scheme["category"] = ""

        if "relevance" not in scheme:
            scheme["relevance"] = ""

        if "benefits" not in scheme:
            scheme["benefits"] = []

        if "eligibility" not in scheme:
            scheme["eligibility"] = []

        if "application_process" not in scheme:
            scheme["application_process"] = []

        if "documents_required" not in scheme:
            scheme["documents_required"] = []

        if "official_url" not in scheme:
            scheme["official_url"] = ""

        if "apply_url" not in scheme:
            scheme["apply_url"] = ""

        # Make sure list fields remain lists.

        list_fields = [
            "benefits",
            "eligibility",
            "application_process",
            "documents_required",
        ]

        for field in list_fields:

            if not isinstance(
                scheme[field],
                list,
            ):

                scheme[field] = [
                    str(scheme[field])
                ]

    return answer


# =========================================================
# Generate answer
# =========================================================

def generate_answer(
    query,
    results,
):

    # -----------------------------------------------------
    # No results
    # -----------------------------------------------------

    if not results:

        return {
            "summary": (
                "I couldn't find any government schemes "
                "matching your query."
            ),

            "schemes": [],

            "important_note": (
                "Try providing more information such as "
                "your state, occupation, age, or type "
                "of assistance."
            ),
        }

    # -----------------------------------------------------
    # Build controlled context
    # -----------------------------------------------------

    context = build_context(
        results
    )

    # -----------------------------------------------------
    # System prompt
    # -----------------------------------------------------

    system_prompt = """
You are an assistant for discovering Indian government schemes.

Answer the user's query using ONLY the schemes provided in the
context.

Do not invent schemes, benefits, eligibility requirements,
documents, application procedures, amounts, dates, or URLs.

Do not assume that the user is eligible.

Return ONLY valid JSON.

The JSON must follow this exact structure:

{
  "summary": "short answer",
  "schemes": [
    {
      "scheme_name": "exact scheme name",
      "state": "state",
      "category": "category",
      "relevance": "why this scheme may be relevant",
      "benefits": ["benefit 1", "benefit 2"],
      "eligibility": ["condition 1", "condition 2"],
      "application_process": ["step 1", "step 2"],
      "documents_required": ["document 1", "document 2"],
      "official_url": "URL",
      "apply_url": "URL"
    }
  ],
  "important_note": "short eligibility disclaimer"
}

RULES:

1. Include at most 3 schemes.
2. Prefer the most relevant schemes.
3. Keep every field concise.
4. Do not repeat unnecessary information.
5. Use only information present in the context.
6. If information is unavailable, use an empty string or empty list.
7. Do not write markdown.
8. Do not use ```json.
9. Return complete valid JSON.
10. Do not stop in the middle of the JSON.
11. Do not assume eligibility.
12. Do not combine information from different schemes.
13. Keep the response concise.
"""

    # -----------------------------------------------------
    # User prompt
    # -----------------------------------------------------

    user_prompt = f"""
USER QUERY:

{query}

CONTEXT:

{context}

Return ONLY the JSON object.
"""

    # -----------------------------------------------------
    # Groq request
    # -----------------------------------------------------

    client = get_groq_client()

    response = client.chat.completions.create(
        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        temperature=0.1,

        max_tokens=2500,
    )

    # -----------------------------------------------------
    # Get response
    # -----------------------------------------------------

    raw_answer = (
        response
        .choices[0]
        .message
        .content
    )

    # -----------------------------------------------------
    # Clean
    # -----------------------------------------------------

    raw_answer = clean_json_response(
        raw_answer
    )

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:

        answer = json.loads(
            raw_answer
        )

    except json.JSONDecodeError:

        print(
            "\nGroq returned invalid JSON:"
        )

        print(
            raw_answer
        )

        raise ValueError(
            "Groq returned invalid JSON."
        )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    answer = validate_answer(
        answer
    )

    return answer