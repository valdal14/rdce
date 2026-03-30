# rdce

[![CI Pipeline](https://github.com/valdal14/rdce/actions/workflows/ci.yml/badge.svg)](https://github.com/valdal14/rdce/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://valdal14.github.io/rdce/)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

**Runtime Data Contract Enforcer**: A lightweight Python 3 library for recursively validating and diffing nested JSON payloads against explicit Pydantic schemas.

## Current Status
🚀 **v0.2.0 Complete** 🚀
The core recursive validation engine, Pydantic extractor, and public API are complete and fully tested with 100% coverage.

## 🌟 Features
* **Pydantic Native:** Define your data contracts using standard Pydantic `BaseModel` classes.
* **Recursive Type Validation:** Deeply inspects nested dictionaries and payloads without flattening them.
* **Array Support:** Natively validates items inside `list[Type]` arrays.
* **Optional Forgiveness:** Gracefully handles missing keys or `None` values for `Optional` and `Union` types.
* **Path Tracking:** Returns exact dot-notation breadcrumbs for schema drift (e.g., `user.address.zip_code`, `nodes[1].ip`).
* **Zero Bloat:** Built to do one thing—diffing data schemas.

---

## 📦 Installation

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

### 3. Validating Arrays and Lists
`rdce` natively supports generic aliases like `list[str]` and lists of nested models. The engine will evaluate every item in the payload array and return the exact index of the violation.

```python
class ServerNode(BaseModel):
    ip_address: str
    is_active: bool

class Cluster(BaseModel):
    cluster_name: str
    nodes: list[ServerNode]

# Payload with an error inside the array at index 1
payload = {
    "cluster_name": "eu-west-db",
    "nodes": [
        {"ip_address": "10.0.0.1", "is_active": True},
        {"ip_address": "10.0.0.2", "is_active": "yes"}
    ]
}

errors = enforce_contract(Cluster, payload)
```

Output:

```json
[{"path": "nodes[1].is_active", "expected": "bool", "actual": "str"}]
```

### 4. Optional and Union Types
rdce gracefully handles optional fields. Missing keys or explicit None values will not trigger false positives if the contract allows them.

```python
from typing import Optional

class UserProfile(BaseModel):
    username: str
    # Modern Python 3.10+ syntax
    age: int | None
    # Classic typing syntax              
    nickname: Optional[str]      

payload = {
    # 'age' is completely missing - ALLOWED!
    "username": "bob_builder",
    # Explicitly null - ALLOWED!
    "nickname": None             
}

errors = enforce_contract(UserProfile, payload)
```

```json
# Output: [] (Perfectly valid payload)
[]
```

---

### 5. Strict Mode Validation
By default, `rdce` ignores extra keys in the payload. To flag injected or unexpected keys that are not defined in your schema, enable `strict=True`.

```python
payload = {
    "username": "bob_builder",
    # INJECTED KEY
    "is_admin": True
}

errors = enforce_contract(UserProfile, payload, strict=True)
# Output: [{"path": "is_admin", "expected": "UNEXPECTED_KEY", "actual": "bool"}]
```

---

### 6. Fast Flat-File Validation (CSV Header Checking)
For data engineering pipelines (like Airflow or Dagster), `rdce` can validate flat-file schema drift without loading the entire file into memory. The `enforce_csv_structure` adapter reads only the first row of a CSV and cross-references the column names against your Pydantic contract.

```python
from rdce.adapters import enforce_csv_structure
from pydantic import BaseModel
from typing import Optional

class PipelineContract(BaseModel):
    id: int
    username: str
    email: Optional[str]

# Instantly catches if an upstream database dropped the 'email' column
errors = enforce_csv_structure(PipelineContract, "massive_export.csv", delimiter=",")
# Output: [{"path": "email", "expected": "COLUMN_PRESENT", "actual": "MISSING"}]
```

---

### 7. Streaming CSV Validation (Deep Scan & Dead-Letter Queues)
When you need to validate data types row-by-row in massive flat files, loading them into memory will cause OOM (Out of Memory) crashes. 

The `stream_csv_contract` adapter acts as a Python Generator. It streams the file one row at a time, attempts basic type coercion, and `yields` only the rows that fail validation. 

This allows you to easily route bad data to a dead-letter queue while letting your pipeline continue:

```python
import csv
from rdce.adapters import stream_csv_contract
from pydantic import BaseModel

class Employee(BaseModel):
    id: int
    name: str
    is_active: bool

# Stream a file, handling enterprise CSV encodings and custom delimiters
bad_rows = stream_csv_contract(
    Employee, 
    "massive_export.csv", 
    delimiter=",", 
    encoding="utf-8-sig", # Automatically strips invisible BOM characters from Excel/Enterprise exports
    ignore_nulls=False
)

# Route the rejected rows to a separate file for review
with open("rejects.csv", "w", newline="") as f:
    writer = None
    
    for bad_row_payload in bad_rows:
        # The payload contains the line number, the exact raw row, and the errors
        raw_row = bad_row_payload["raw_row"]
        errors = bad_row_payload["errors"]
        
        # Initialize the CSV writer on the first bad row we find
        if writer is None:
            writer = csv.DictWriter(f, fieldnames=raw_row.keys())
            writer.writeheader()
            
        writer.writerow(raw_row)
        print(f"Row {bad_row_payload['line_num']} failed: {errors}")
```

---

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