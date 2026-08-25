# app/rag/search.py

from app.rag.vector_store import load_vector_store
from app.rag.query_parser import parse_query
from app.rag.answer_generator import generate_answer


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
        "eligibility_state",
        "",
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

    # Explicit Central / All-India markers
    if state in {
        "central",
        "all india",
        "all-india",
        "india",
        "government of india",
    }:
        return True

    # Empty state + empty eligibility state
    # is treated as Central / All-India.
    if (
        not state
        and not any(normalized_states)
    ):
        return True

    return False


# =========================================================
# State Matching
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

    requested_state = (
        requested_state
        .strip()
        .lower()
    )

    metadata = document.metadata

    # Central schemes are valid for state queries.
    if is_central_scheme(document):
        return True

    document_state = str(
        metadata.get(
            "state",
            "",
        )
    ).strip().lower()

    if requested_state == document_state:
        return True

    eligibility_state = metadata.get(
        "eligibility_state",
        "",
    )

    if isinstance(
        eligibility_state,
        list,
    ):

        for state in eligibility_state:

            if (
                requested_state
                == str(state).strip().lower()
            ):
                return True

    else:

        normalized_eligibility_state = (
            str(
                eligibility_state
            ).strip().lower()
        )

        if (
            requested_state
            == normalized_eligibility_state
        ):
            return True

    return False


# =========================================================
# Category Matching
# =========================================================

def category_matches(
    document,
    requested_category,
):
    """
    Check whether a scheme belongs to the requested category.

    Dataset categories may contain multiple categories, for example:

        Agriculture,Rural & Environment, Business & Entrepreneurship

    Therefore the requested category is matched against the
    individual category components.
    """

    if not requested_category:
        return True

    document_category = str(
        document.metadata.get(
            "category",
            "",
        )
    ).strip().lower()

    if not document_category:
        return False

    requested_categories = [
        item.strip().lower()
        for item in requested_category.split(",")
        if item.strip()
    ]

    document_categories = [
        item.strip().lower()
        for item in document_category.split(",")
        if item.strip()
    ]

    for requested in requested_categories:

        for document_category_item in document_categories:

            if (
                requested
                == document_category_item
            ):
                return True

    return False


# =========================================================
# Search Schemes
# =========================================================

def search_schemes(
    query: str,
    semantic_k: int = 100,
    final_k: int = 5,
):
    """
    Retrieve government schemes for one user query.

    Pipeline:

    1. Parse query.
    2. Perform semantic search.
    3. Filter by state.
    4. Filter by category.
    5. Return the best matching schemes.

    No BM25.
    No score fusion.
    No reranking.
    """

    # -----------------------------------------------------
    # Step 1: Parse query
    # -----------------------------------------------------

    parsed_query = parse_query(
        query
    )

    print(
        "\nParsed query:"
    )

    print(
        parsed_query
    )

    requested_state = parsed_query.get(
        "state"
    )

    requested_category = parsed_query.get(
        "category"
    )

    # -----------------------------------------------------
    # Step 2: Load vector store
    # -----------------------------------------------------

    vector_store = load_vector_store()

    # -----------------------------------------------------
    # Step 3: Semantic search
    # -----------------------------------------------------

    print(
        f"\nSemantic search: retrieving top "
        f"{semantic_k} schemes..."
    )

    semantic_results = (
        vector_store.similarity_search_with_score(
            query,
            k=semantic_k,
        )
    )

    print(
        "Semantic candidates:",
        len(semantic_results),
    )

    if not semantic_results:
        return []

    # -----------------------------------------------------
    # Step 4: State filtering
    # -----------------------------------------------------

    state_filtered = []

    for document, distance in semantic_results:

        if state_matches(
            document,
            requested_state,
        ):

            state_filtered.append(
                (
                    document,
                    distance,
                )
            )

    print(
        "After state filter:",
        len(state_filtered),
    )

    # -----------------------------------------------------
    # Step 5: Category filtering
    # -----------------------------------------------------

    category_filtered = []

    for document, distance in state_filtered:

        if category_matches(
            document,
            requested_category,
        ):

            category_filtered.append(
                (
                    document,
                    distance,
                )
            )

    print(
        "After category filter:",
        len(category_filtered),
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Do NOT blindly fall back to state-only results.
    # -----------------------------------------------------

    if (
        requested_category
        and not category_filtered
    ):

        print(
            "\nNo schemes matched both "
            "state and category."
        )

        return []

    # -----------------------------------------------------
    # Step 6: Sort by semantic distance
    # -----------------------------------------------------

    category_filtered.sort(
        key=lambda item: item[1]
    )

    # -----------------------------------------------------
    # Step 7: Select final results
    # -----------------------------------------------------

    results = []

    for document, distance in category_filtered[
        :final_k
    ]:

        results.append(
            {
                "document": document,
                "distance": distance,
            }
        )

    return results


# =========================================================
# Print Results
# =========================================================

def print_results(results):
    """
    Print retrieved schemes for local debugging.
    """

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RETRIEVED SCHEMES"
    )

    print(
        "=" * 70
    )

    if not results:

        print(
            "\nNo matching schemes found."
        )

        return

    for index, result in enumerate(
        results,
        start=1,
    ):

        document = result[
            "document"
        ]

        metadata = document.metadata

        print(
            f"\nResult {index}"
        )

        print(
            "-" * 70
        )

        print(
            "Scheme:",
            metadata.get(
                "scheme_name",
                "Unknown",
            ),
        )

        print(
            "State:",
            metadata.get(
                "state",
                "",
            ),
        )

        print(
            "Category:",
            metadata.get(
                "category",
                "",
            ),
        )

        print(
            "Semantic distance:",
            round(
                result["distance"],
                4,
            ),
        )


# =========================================================
# Main
# =========================================================

def main():

    # -----------------------------------------------------
    # One query at a time.
    # -----------------------------------------------------

    query = input(
        "\nSearch query:\n"
    ).strip()

    if not query:

        print(
            "\nQuery cannot be empty."
        )

        return

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    results = search_schemes(
        query=query,
        semantic_k=100,
        final_k=5,
    )

    # -----------------------------------------------------
    # Display retrieval results
    # -----------------------------------------------------

    print_results(
        results
    )

    # -----------------------------------------------------
    # Generate answer
    # -----------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "GENERATING ANSWER WITH GROQ..."
    )

    print(
        "=" * 70
    )

    try:

        answer = generate_answer(
            query,
            results,
        )

    except Exception as error:

        print(
            "\nERROR GENERATING ANSWER:"
        )

        print(
            error
        )

        return

    # -----------------------------------------------------
    # Display JSON answer
    # -----------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "GENERATED ANSWER"
    )

    print(
        "=" * 70
    )

    print(
        answer
    )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    main()