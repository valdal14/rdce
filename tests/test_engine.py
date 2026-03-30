from rdce.engine import compare_payload


def test_flat_dictionary_match():
    schema = {"name": "str", "age": "int"}
    payload = {"name": "Alice", "age": 30}
    # Should return an empty list because everything matches
    assert compare_payload(schema, payload) == []


def test_flat_dictionary_type_mismatch():
    schema = {"name": "str", "age": "int"}
    payload = {"name": "Alice", "age": "thirty"}

    errors = compare_payload(schema, payload)

    assert len(errors) == 1
    assert errors[0] == {"path": "age", "expected": "int", "actual": "str"}


def test_missing_field_in_payload():
    schema = {"name": "str", "age": "int", "active": "bool"}
    payload = {"name": "Alice"}

    errors = compare_payload(schema, payload)

    assert len(errors) == 2
    # We expect errors for both missing fields
    paths = [err["path"] for err in errors]
    assert "age" in paths
    assert "active" in paths
    assert errors[0]["actual"] == "MISSING"


def test_nested_dictionary_mismatch():
    schema = {"user": {"id": "int", "metadata": {"is_admin": "bool"}}}
    payload = {
        "user": {
            "id": 123,
            "metadata": {
                "is_admin": "yes"  # This is a string, schema expects a bool
            },
        }
    }

    errors = compare_payload(schema, payload)

    assert len(errors) == 1
    assert errors[0] == {"path": "user.metadata.is_admin", "expected": "bool", "actual": "str"}


def test_compare_optional_and_union_types():
    schema = {
        "age": ("int", "NoneType"),
        "nickname": ("str", "NoneType"),
        # A pure union, no NoneType allowed
        "status": ("str", "int"),
    }

    payload = {
        # 'age' is completely missing! (Should pass because NoneType is in the tuple)
        # Provided as null/None (Should pass)
        "nickname": None,
        # ERROR: Provided a boolean, expects str or int
        "status": True,
    }

    errors = compare_payload(schema, payload)

    assert len(errors) == 1
    assert errors[0] == {"path": "status", "expected": "('str', 'int')", "actual": "bool"}

def test_compare_strict_mode():
    schema = {
        "username": "str",
        "profile": {"age": "int"}
    }
    
    payload = {
        "username": "admin",
        # INJECTED KEY (Root level)
        "is_superuser": True,        
        "profile": {
            "age": 30,
            # INJECTED KEY (Nested level)
            "role": "manager"        
        }
    }
    
    # Standard mode should ignore the extra keys and pass perfectly
    standard_errors = compare_payload(schema, payload)
    assert len(standard_errors) == 0
    
    # Strict mode should catch both injected keys
    strict_errors = compare_payload(schema, payload, strict=True)
    assert len(strict_errors) == 2
    
    paths = [err["path"] for err in strict_errors]
    assert "is_superuser" in paths
    assert "profile.role" in paths
    
    # Verify the error format for the first injected key
    assert strict_errors[0] == {"path": "is_superuser", "expected": "UNEXPECTED_KEY", "actual": "bool"}

def test_strict_mode_multiple_injected_keys():
    schema = {
        "username": "str"
    }
    
    payload = {
        "username": "admin",
        "is_superuser": True,    # Injected Key 1
        "bypass_auth": True      # Injected Key 2
    }
    
    errors = compare_payload(schema, payload, strict=True)
    
    # It will only find 1 error and exit, ignoring the second key entirely!
    assert len(errors) == 2
    
    paths = [err["path"] for err in errors]
    assert "is_superuser" in paths
    assert "bypass_auth" in paths