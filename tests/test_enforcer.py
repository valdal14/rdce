from pydantic import BaseModel

from rdce.enforcer import enforce_contract


class ServerConfig(BaseModel):
    host: str
    port: int
    is_https: bool


def test_enforce_contract_success():
    payload = {"host": "localhost", "port": 8080, "is_https": True}

    # Should return an empty list because the payload is perfect
    errors = enforce_contract(ServerConfig, payload)
    assert errors == []


def test_enforce_contract_with_errors():
    payload = {
        "host": "localhost",
        "port": "8080",  # String instead of int
        # is_https is missing entirely
    }

    errors = enforce_contract(ServerConfig, payload)

    assert len(errors) == 2
    paths = [err["path"] for err in errors]
    assert "port" in paths
    assert "is_https" in paths
