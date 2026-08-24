# app/rag/search.py

import logging

from app.rag.lightweight_store import keyword_search
from app.rag.query_parser import parse_query
from app.rag.eligibility import evaluate_eligibility


logger = logging.getLogger(__name__)


# =========================================================
# Central Scheme Detection
# =========================================================

def is_central_scheme(document):
    """
    Determine whether a scheme is a Central / All-India scheme.
    """

    metadata = document.metadata

    state = str(
        metadata.get("state", "")
    ).strip().lower()

    eligibility_state = metadata.get(
        "eligibility_state", "",
    )

    if isinstance(eligibility_state, list):
        normalized_states = [
            str(item).strip().lower()
            for item in eligibility_state
        ]
    else:
        normalized_states = [
            str(eligibility_state).strip().lower()
        ]

    if state in {
        "central",
        "all india",
        "all-india",
        "india",
        "government of india",
    }:
        return True

    # Empty state + empty eligibility_state → treated as Central.
    if not state and not any(normalized_states):
        return True

    return False


# =========================================================
# State Matching  (Python-side secondary guard)
# =========================================================

def state_matches(document, requested_state):
    """
    Check whether a scheme applies to the requested state.

    A scheme matches when:
      1. It is a Central / All-India scheme.
      2. Its state exactly matches the requested state.
      3. Its eligibility_state contains the requested state.
    """

    if not requested_state:
        return True

    requested_state = requested_state.strip().lower()

    metadata = document.metadata

    if is_central_scheme(document):
        return True

    document_state = str(
        metadata.get("state", "")
    ).strip().lower()

    if requested_state == document_state:
        return True

    eligibility_state = metadata.get("eligibility_state", "")

    if isinstance(eligibility_state, list):
        for state in eligibility_state:
            if requested_state == str(state).strip().lower():
                return True
    else:
        if requested_state == str(eligibility_state).strip().lower():
            return True

    return False


# =========================================================
# Category Matching  (Python-side secondary guard)
# =========================================================

def category_matches(document, requested_category):
    """
    Check whether a scheme belongs to the requested category.

    Dataset categories may contain multiple values, e.g.:
        "Agriculture,Rural & Environment, Business & Entrepreneurship"

    The requested category is matched against individual components.
    """

    if not requested_category:
        return True

    document_category = str(
        document.metadata.get("category", "")
    ).strip().lower()

    if not document_category:
        return False

    requested_parts = [
        item.strip().lower()
        for item in requested_category.split(",")
        if item.strip()
    ]

    document_parts = [
        item.strip().lower()
        for item in document_category.split(",")
        if item.strip()
    ]

    for req in requested_parts:
        for doc_part in document_parts:
            if req == doc_part:
                return True

    return False


# =========================================================
# Build Chroma where clause
# =========================================================

def build_where_clause(state, category=None):
    """
    Build a Chroma metadata filter to push state
    filtering onto the full corpus before scoring.

    Returns a where dict or None if no filters apply.
    """

    if state:
        # Match exact state or central/all-india markers using $in
        return {
            "state": {"$in": [state, "Central", "All India", ""]}
        }

    return None


# =========================================================
# Search Schemes
# =========================================================

def search_schemes(
    query: str,
    final_k: int = 5,
):
    """
    Retrieve government schemes for one user query.

    Pipeline:
      1. Parse query (state, category, age, gender, income).
      2. Semantic search with Chroma where-clause on full corpus.
      3. Python-side secondary guard (central-scheme detection,
         multi-value eligibility_state lists).
      4. Evaluate eligibility (age / gender / income).
      5. Sort by eligibility score then semantic distance.
      6. Return the best final_k results.
    """

    # --------------------------------------------------
    # Step 1: Parse query
    # --------------------------------------------------

    parsed = parse_query(query)

    requested_state    = parsed.get("state")
    requested_category = parsed.get("category")
    user_profile = {
        "age":    parsed.get("age"),
        "gender": parsed.get("gender"),
        "income": parsed.get("income"),
    }

    logger.info("Parsed query: %s", parsed)

    # --------------------------------------------------
    # Step 2: Search the bundled SQLite full-text index
    # --------------------------------------------------

    # The data file includes an FTS index, so no Torch model or Chroma server
    # needs to be loaded at runtime.
    semantic_results = keyword_search(query, k=50)

    logger.info("Semantic candidates: %d", len(semantic_results))

    if not semantic_results:
        logger.info("no_match_reason=no_results (Chroma returned nothing)")
        return {
            "results": [],
            "no_match_reason": "no_results",
            "parsed": parsed,
        }

    # --------------------------------------------------
    # Step 4: Python-side secondary guard
    # --------------------------------------------------

    state_filtered = [
        (doc, dist)
        for doc, dist in semantic_results
        if state_matches(doc, requested_state)
    ]

    logger.info("After state filter: %d", len(state_filtered))

    category_filtered = [
        (doc, dist)
        for doc, dist in state_filtered
        if category_matches(doc, requested_category)
    ]

    logger.info("After category filter: %d", len(category_filtered))

    if requested_category and not category_filtered:
        reason = (
            "parser_miss"
            if state_filtered
            else "no_results"
        )
        logger.info(
            "no_match_reason=%s  requested_category=%s",
            reason,
            requested_category,
        )
        return {
            "results": [],
            "no_match_reason": reason,
            "parsed": parsed,
        }

    # --------------------------------------------------
    # Step 5: Evaluate eligibility
    # --------------------------------------------------

    scored = []

    any_profile_data = any(user_profile.values())

    for document, distance in category_filtered:

        result = {
            "document": document,
            "distance": distance,
            "eligibility": None,
        }

        if any_profile_data:
            eligibility = evaluate_eligibility(document, user_profile)
            result["eligibility"] = eligibility

            # Hard-fail: drop schemes the user clearly cannot access.
            if eligibility.get("eligible") is False:
                continue

        scored.append(result)

    # --------------------------------------------------
    # Step 6: Sort — eligibility score desc, distance asc
    # --------------------------------------------------

    def sort_key(r):
        elig = r.get("eligibility") or {}
        elig_score = elig.get("score", 0.0)
        # Higher eligibility score is better; lower distance is better.
        return (-elig_score, r["distance"])

    scored.sort(key=sort_key)

    return {
        "results": scored[:final_k],
        "no_match_reason": None,
        "parsed": parsed,
    }
