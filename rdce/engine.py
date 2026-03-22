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
        # Update the breadcrumb path
        if current_path == "":
            path = key
        else:
            path = f"{current_path}.{key}"

        # Check if the key is missing from the cargo
        if key not in payload:
            # Forgive the missing key if the schema is a tuple that allows "NoneType"
            if isinstance(expected_type, tuple) and "NoneType" in expected_type:
                continue
            else:
                # Log the missing key error
                errors.append(_build_error(path, str(expected_type), "MISSING"))
                continue

        # The key exists we can safely get the value
        actual_value = payload[key]

        # Check if it a branch (The schema expects a nested dictionary)
        if isinstance(expected_type, dict):
            res = compare_payload(expected_type, actual_value, path)
            errors.extend(res)

        # Check if this is an Array (The schema expects a list)
        elif isinstance(expected_type, list):
            # Ensure the payload actually gave us a list
            if not isinstance(actual_value, list):
                errors.append(_build_error(path, "list", type(actual_value).__name__))
                continue
            
            # The schema list only has ONE rule (e.g., ["str"] or [{"ip": "str"}])
            inner_schema = expected_type[0]
            
            # Loop through every item in the payload's array
            for index, item in enumerate(actual_value):
                list_path = f"{path}[{index}]"
                
                # If the inner rule is a dictionary, recurse.
                if isinstance(inner_schema, dict):
                    errors.extend(compare_payload(inner_schema, item, list_path))
                # Otherwise, it's a primitive and we can check its type.
                else:
                    item_type_string = type(item).__name__
                    if item_type_string != inner_schema:
                        errors.append(_build_error(list_path, inner_schema, item_type_string))

        # Check if this is an Optional/Union (The schema expects a tuple of choices)
        elif isinstance(expected_type, tuple):
            actual_type_string = type(actual_value).__name__
            # If the actual type isn't one of the allowed choices in the tuple log the error.
            if actual_type_string not in expected_type:
                errors.append(_build_error(path, str(expected_type), actual_type_string))

        # Normal primitive (leaf node)
        else:
            actual_type_string = type(actual_value).__name__
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
