# rdce

[![CI Pipeline](https://github.com/valdal14/rdce/actions/workflows/ci.yml/badge.svg)](https://github.com/valdal14/rdce/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

**Runtime Data Contract Enforcer**: A lightweight Python 3 library for recursively validating and diffing nested JSON payloads against explicit Pydantic schemas.

## Current Status
🚀 **v0.1.0 Complete** 🚀
The core recursive validation engine, Pydantic extractor, and public API are complete and fully tested with 100% coverage.

## 🌟 Features
* **Pydantic Native:** Define your data contracts using standard Pydantic `BaseModel` classes.
* **Recursive Type Validation:** Deeply inspects nested dictionaries and payloads without flattening them.
* **Path Tracking:** Returns exact dot-notation breadcrumbs for schema drift (e.g., `user.address.zip_code`).
* **Zero Bloat:** Built to do one thing perfectly—diffing data schemas.

---

## 📦 Installation

*(Note: Pending PyPI release)*
```bash
pip install rdce
# Or using poetry
poetry add rdce
```

---

## 🚀 Quick Start
`rdce` is designed to be a transparent bridge between your Pydantic models and incoming, untrusted dictionary payloads.

### 1. Define your Contract
Use standard Pydantic models. Nested models are fully supported.

```python
from pydantic import BaseModel

class Address(BaseModel):
    city: str
    zip_code: int

class UserContract(BaseModel):
    username: str
    is_active: bool
    address: Address
```

### 2. Enforce the Payload
Pass the model class and your raw dictionary payload into the `enforce_contract` engine.

```python
from rdce import enforce_contract

# A payload with schema drift (wrong type for zip_code, missing is_active)
incoming_payload = {
    "username": "alice_data",
    "address": {
        "city": "London",
        "zip_code": "E1 6AN" # Expected int, got string
    }
}

errors = enforce_contract(UserContract, incoming_payload)

for error in errors:
    print(error)
```

Output:

```json
[
  {"path": "is_active", "expected": "bool", "actual": "MISSING"},
  {"path": "address.zip_code", "expected": "int", "actual": "str"}
]
```

## 🤝 Contributing
We welcome contributions! To set up the project locally:

```bash
1 Clone the repository.
2 Initialize the environment: poetry install
3 We strictly enforce formatting and linting via Ruff:
4 Linter: 
    poetry run python3 -m ruff check .
5 Formatter: 
    poetry run python3 -m ruff format .
6 Run the test suite: 
    poetry run pytest
7 Ensure 100% test coverage before submitting a Pull Request.
```

