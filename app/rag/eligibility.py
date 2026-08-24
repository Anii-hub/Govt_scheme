def normalize_gender(value):
    if not value:
        return None

    value = str(value).strip().lower()

    aliases = {
        "male": "male",
        "man": "male",
        "boy": "male",

        "female": "female",
        "woman": "female",
        "girl": "female",

        "all": "all",
        "any": "all",
        "both": "all",
    }

    return aliases.get(value, value)


def normalize_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def check_age(document, user_age):
    """
    Returns:
        True  -> user clearly satisfies age requirement
        False -> user clearly fails age requirement
        None  -> insufficient information
    """

    if user_age is None:
        return None

    metadata = document.metadata

    min_age = normalize_number(
        metadata.get("eligibility_age_min")
    )

    max_age = normalize_number(
        metadata.get("eligibility_age_max")
    )

    user_age = normalize_number(user_age)

    if user_age is None:
        return None

    if min_age is not None and user_age < min_age:
        return False

    if max_age is not None and user_age > max_age:
        return False

    return True


def check_gender(document, user_gender):
    """
    Check gender eligibility.

    Returns:
        True  -> matches
        False -> conflicts
        None  -> insufficient information
    """

    if not user_gender:
        return None

    user_gender = normalize_gender(
        user_gender
    )

    scheme_gender = normalize_gender(
        document.metadata.get(
            "eligibility_gender"
        )
    )

    if not scheme_gender:
        return None

    if scheme_gender == "all":
        return True

    if user_gender == scheme_gender:
        return True

    return False


def check_income(document, user_income):
    """
    Check maximum income eligibility.
    """

    if user_income is None:
        return None

    scheme_max_income = normalize_number(
        document.metadata.get(
            "eligibility_income_max"
        )
    )

    user_income = normalize_number(
        user_income
    )

    if scheme_max_income is None:
        return None

    if user_income <= scheme_max_income:
        return True

    return False


def evaluate_eligibility(
    document,
    user_profile,
):
    """
    Evaluate known eligibility information.

    Unknown information does NOT automatically fail.

    Returns:
        {
            "eligible": True/False/None,
            "score": float,
            "checks": {...}
        }
    """

    checks = {}

    age_result = check_age(
        document,
        user_profile.get("age"),
    )

    gender_result = check_gender(
        document,
        user_profile.get("gender"),
    )

    income_result = check_income(
        document,
        user_profile.get("income"),
    )

    checks["age"] = age_result
    checks["gender"] = gender_result
    checks["income"] = income_result

    # -----------------------------------------------------
    # Hard failures
    # -----------------------------------------------------

    for result in checks.values():

        if result is False:

            return {
                "eligible": False,
                "score": 0.0,
                "checks": checks,
            }

    # -----------------------------------------------------
    # Score known matching conditions
    # -----------------------------------------------------

    known_checks = [
        result
        for result in checks.values()
        if result is not None
    ]

    if not known_checks:

        return {
            "eligible": None,
            "score": 0.0,
            "checks": checks,
        }

    matched = sum(
        1
        for result in known_checks
        if result is True
    )

    score = matched / len(
        known_checks
    )

    return {
        "eligible": True,
        "score": score,
        "checks": checks,
    }