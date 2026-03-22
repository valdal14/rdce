from typing import Optional

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


def test_extract_list_primitives():
    class Product(BaseModel):
        name: str
        tags: list[str]

    schema = extract_schema(Product)

    assert schema == {"name": "str", "tags": ["str"]}


def test_extract_list_models():
    class Address(BaseModel):
        city: str

    class User(BaseModel):
        addresses: list[Address]

    schema = extract_schema(User)

    assert schema == {"addresses": [{"city": "str"}]}


def test_extract_optional_and_union_types():
    class UserProfile(BaseModel):
        username: str
        # Adding both ways of handling optional
        # to check library compatibility

        # The modern Python 3.10+ syntax
        age: int | None
        # The classic typing module syntax
        nickname: Optional[str]

    schema = extract_schema(UserProfile)

    assert schema == {
        "username": "str",
        "age": ("int", "NoneType"),
        "nickname": ("str", "NoneType"),
    }
