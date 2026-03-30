import logging
from typing import Any

from .error_factory import build_error

logger = logging.getLogger("rdce")


def compare_payload(
    schema: dict[str, Any], payload: dict[str, Any], current_path: str = "", strict: bool = False
) -> list[dict[str, str]]:
    """
    Recursively compares a payload dictionary against an expected schema dictionary.

    Args:
        schema (dict[str, Any]): The expected data contract defining fields and types.
        payload (dict[str, Any]): The actual incoming data payload.
        current_path (str, optional): The current path traversal state. Defaults to "".
        strict (bool, optional): If True, flags extra keys in the payload not defined in the schema.

    Returns:
        list[dict[str, str]]: A list of validation errors. Returns an empty list if perfectly matched.
    """
    # Only log at the very beginning of the validation
    if current_path == "":
        logger.debug(f"Starting payload validation. Strict mode: {strict}")

    errors = []

    # Strict mode check
    strict_errors = _strict_mode_check(schema, payload, current_path, strict)
    errors.extend(strict_errors)

    # Standard mode iteration
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
                logger.debug(f"Validation failure: Missing required key '{path}'")
                errors.append(build_error(path, str(expected_type), "MISSING"))
                continue

        # The key exists we can safely get the value
        actual_value = payload[key]

        # Check if it a branch (The schema expects a nested dictionary)
        if isinstance(expected_type, dict):
            res = compare_payload(expected_type, actual_value, path, strict)
            errors.extend(res)

        # Check if this is an Array (The schema expects a list)
        elif isinstance(expected_type, list):
            # Ensure the payload actually gave us a list
            if not isinstance(actual_value, list):
                logger.debug(
                    f"Validation failure: '{path}' expected list, got {type(actual_value).__name__}"
                )
                errors.append(build_error(path, "list", type(actual_value).__name__))
                continue

            # The schema list only has ONE rule (e.g., ["str"] or [{"ip": "str"}])
            inner_schema = expected_type[0]

            # Loop through every item in the payload's array
            for index, item in enumerate(actual_value):
                list_path = f"{path}[{index}]"

                # If the inner rule is a dictionary, recurse.
                if isinstance(inner_schema, dict):
                    errors.extend(compare_payload(inner_schema, item, list_path, strict))
                # Otherwise, it's a primitive and we can check its type.
                else:
                    item_type_string = type(item).__name__
                    if item_type_string != inner_schema:
                        logger.debug(
                            f"Validation failure: '{list_path}' expected {inner_schema}, got {item_type_string}"
                        )
                        errors.append(build_error(list_path, inner_schema, item_type_string))

        # Check if this is an Optional/Union (The schema expects a tuple of choices)
        elif isinstance(expected_type, tuple):
            actual_type_string = type(actual_value).__name__
            # If the actual type isn't one of the allowed choices in the tuple log the error.
            if actual_type_string not in expected_type:
                logger.debug(
                    f"Validation failure: '{path}' expected {expected_type}, got {actual_type_string}"
                )
                errors.append(build_error(path, str(expected_type), actual_type_string))

        # Normal primitive (leaf node)
        else:
            actual_type_string = type(actual_value).__name__
            if actual_type_string != expected_type:
                logger.debug(
                    f"Validation failure: '{path}' expected {expected_type}, got {actual_type_string}"
                )
                errors.append(build_error(path, expected_type, actual_type_string))

    return errors


# NOTE: - Internal Helper Methods #################################################################


def _strict_mode_check(
    schema: dict[str, Any], payload: dict[str, Any], current_path: str = "", strict: bool = False
) -> list[dict[str, str]]:
    """
    Checks the payload for injected or unexpected keys not defined in the schema.

    Args:
        schema (dict[str, Any]): The expected data contract defining fields and types.
        payload (dict[str, Any]): The actual incoming data payload.
        current_path (str, optional): The current path traversal state. Defaults to "".
        strict (bool, optional): If True, flags extra keys in the payload not defined in the schema.

    Returns:
        list[dict[str, str]]: Empty if strict mode is False or the key is in the schema
    """
    strict_errors = []

    if strict:
        for payload_key, payload_value in payload.items():
            if payload_key not in schema:
                # Build the path for the injected key
                if current_path == "":
                    path = payload_key
                else:
                    path = f"{current_path}.{payload_key}"

                # Log the unexpected key
                actual_type_string = type(payload_value).__name__
                logger.warning(f"Strict Mode violation: Unexpected key '{path}' detected.")
                strict_errors.append(build_error(path, "UNEXPECTED_KEY", actual_type_string))

    return strict_errors
