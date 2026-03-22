from typing import Any

from pydantic import BaseModel


def extract_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Translates a Pydantic model into a raw schema dictionary.

    Args:
        model (type[BaseModel]): The Pydantic class to inspect.

    Returns:
        dict[str, Any]: A nested dictionary representing the expected types.
    """
    schema = {}

    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation

        # Check if it is another Pydantic model
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            schema[field_name] = extract_schema(field_type)
        else:
            schema[field_name] = field_type.__name__

    return schema
