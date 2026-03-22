from typing import Any, get_args, get_origin, Union
from types import UnionType
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

        # Check if this field is another Pydantic model
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            schema[field_name] = extract_schema(field_type)

        # Check if this is a list
        elif get_origin(field_type) is list:
            # Look inside the list to find the inner type
            inner_type = get_args(field_type)[0]

            # Check if the inner type a nested model (e.g., list[Address])
            if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                # Recurse, but wrap the result in a list
                schema[field_name] = [extract_schema(inner_type)]
            else:
                # It's a list of normal primitives
                schema[field_name] = [inner_type.__name__]

        # Check if this is an Optional/Union (e.g., int | None)
        elif get_origin(field_type) in (Union, UnionType):
            # Grab the inner types (e.g., 'int' and 'NoneType')
            inner_types = get_args(field_type)
            
            # Create a tuple of their string names
            # You can do this with a simple list comprehension or a small loop!
            schema[field_name] = tuple(t.__name__ for t in inner_types)

        # It's a normal primitive (like str, int, bool)
        else:
            schema[field_name] = field_type.__name__

    return schema
