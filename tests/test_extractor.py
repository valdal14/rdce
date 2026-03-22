from pydantic import BaseModel

from rdce.extractor import extract_schema


# Define Pydantic models for testing
class Address(BaseModel):
    city: str
    zip_code: int


class User(BaseModel):
    name: str
    is_active: bool
    address: Address


# NOTE: Extractor Tests ############################
def test_extract_flat_model():
    class SimpleModel(BaseModel):
        id: int
        title: str

    schema = extract_schema(SimpleModel)

    assert schema == {"id": "int", "title": "str"}


def test_extract_nested_model():
    schema = extract_schema(User)

    assert schema == {
        "name": "str",
        "is_active": "bool",
        "address": {"city": "str", "zip_code": "int"},
    }
