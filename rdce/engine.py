from typing import Any


def compare_payload(
    schema: dict[str, Any], payload: dict[str, Any], current_path: str = ""
) -> list[dict[str, str]]:
    """
    Recursively compares a payload dictionary against an expected schema dictionary.

    Args:
        schema (dict[str, Any]): The expected data contract defining fields and types.
        payload (dict[str, Any]): The actual incoming data payload.
        current_path (str, optional): The current path traversal state. Defaults to "".

    Returns:
        list[dict[str, str]]: A list of validation errors. Returns an empty list if perfectly matched.
    """
    errors = []

    for key, expected_type in schema.items():
        if current_path == "":
            path = key
        else:
            path = f"{current_path}.{key}"

        if key not in payload:
            # Log the missing key error
            errors.append(_build_error(path, str(expected_type), "MISSING"))
            # skip to the next key in the schema
            continue

        actual_value = payload[key]

        # Check if this is a branch (The schema expects a dictionary)
        if isinstance(expected_type, dict):
            res = compare_payload(expected_type, actual_value, path)
            errors.extend(res)
        else:
            # Get the actual type of the payload's value as a string
            actual_type_string = type(actual_value).__name__

            # Compare it to what the schema asked for
            if actual_type_string != expected_type:
                errors.append(_build_error(path, expected_type, actual_type_string))

    return errors


def _build_error(path: str, expected_type: str, actual: str) -> dict[str, str]:
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
