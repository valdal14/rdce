from typing import Any

from pydantic import BaseModel

from .engine import compare_payload
from .extractor import extract_schema


def enforce_contract(contract: type[BaseModel], payload: dict[str, Any]) -> list[dict[str, str]]:
    schema = extract_schema(contract)
    return compare_payload(schema, payload)
