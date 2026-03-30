def build_error(path: str, expected_type: str, actual: str) -> dict[str, str]:
    """
    Constructs a standardized validation error dictionary.

    Args:
        path (str): The dot-notation breadcrumb path of the failing field.
        expected_type (str): The Python type expected by the schema.
        actual (str): The actual type received, or "MISSING" if not found.

    Returns:
        dict[str, str]: The formatted error payload.
    """
    return {"path": path, "expected": expected_type, "actual": actual}
