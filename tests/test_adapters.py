import csv

from pydantic import BaseModel

from rdce.adapters import enforce_csv_structure


class UserContract(BaseModel):
    id: int
    username: str
    email: str


def test_enforce_csv_structure_valid(tmp_path):
    # Create a temporary CSV file
    file_path = tmp_path / "valid.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["id", "username", "email"])
        # Data
        writer.writerow(["1", "alice", "a@example.com"])

    # Should pass perfectly
    errors = enforce_csv_structure(UserContract, str(file_path))
    assert len(errors) == 0


def test_enforce_csv_structure_drift(tmp_path):
    file_path = tmp_path / "drift.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        # We dropped 'email', renamed 'username' to 'user_name', and added 'role'
        writer.writerow(["id", "user_name", "role"])

    errors = enforce_csv_structure(UserContract, str(file_path))

    # We should catch the two missing columns ('username' and 'email')
    assert len(errors) == 2
    paths = [err["path"] for err in errors]
    assert "username" in paths
    assert "email" in paths
