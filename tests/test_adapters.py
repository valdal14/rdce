import csv

from pydantic import BaseModel

from rdce.adapters import enforce_csv_structure, stream_csv_contract


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


def test_stream_csv_contract_yields_bad_rows(tmp_path):
    class Employee(BaseModel):
        emp_id: int
        name: str
        is_active: bool
        score: float | None

    file_path = tmp_path / "employees.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        # Line 1: Header
        writer.writerow(["emp_id", "name", "is_active", "score"])
        # Line 2: Perfect row
        writer.writerow(["1", "Alice", "true", "95.5"])
        # Line 3: Error -> 'emp_id' is not an integer
        writer.writerow(["two", "Bob", "false", "80.0"])
        # Line 4: Perfect row -> 'yes' coerced to True, 'NaN' coerced to None
        writer.writerow(["3", "Charlie", "yes", "NaN"])
        # Line 5: Error -> 'name' is empty/null, but schema says it is required (str)
        writer.writerow(["4", "", "0", ""])

    # We convert the generator to a list so we can easily inspect the yielded rejects
    rejects = list(stream_csv_contract(Employee, str(file_path), null_markers=["", "NaN"]))

    # It should completely ignore Alice and Charlie, yielding only Bob and the empty name row
    assert len(rejects) == 2

    # Inspect Bob's failure (Line 3)
    assert rejects[0]["line_num"] == 3
    assert rejects[0]["raw_row"]["name"] == "Bob"
    assert rejects[0]["errors"][0]["path"] == "emp_id"
    assert rejects[0]["errors"][0]["expected"] == "int"

    # Inspect the missing name failure (Line 5)
    assert rejects[1]["line_num"] == 5
    assert rejects[1]["errors"][0]["path"] == "name"
    assert rejects[1]["errors"][0]["actual"] == "NULL"


def test_stream_csv_perfect_file(tmp_path):
    """Ensures a completely valid file yields absolutely nothing."""

    class SimpleContract(BaseModel):
        id: int
        name: str

    file_path = tmp_path / "perfect.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name"])
        writer.writerow(["1", "Alice"])
        writer.writerow(["2", "Bob"])

    rejects = list(stream_csv_contract(SimpleContract, str(file_path)))
    assert len(rejects) == 0


def test_stream_csv_structural_abort(tmp_path):
    """Ensures that if the header is wrong, it aborts instantly without scanning rows."""

    class SimpleContract(BaseModel):
        id: int
        name: str

    file_path = tmp_path / "bad_header.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "WRONG_COLUMN"])  # Missing 'name'
        writer.writerow(["1", "Alice"])
        writer.writerow(["2", "Bob"])

    rejects = list(stream_csv_contract(SimpleContract, str(file_path)))

    # It should yield exactly ONE payload (the structural error) and then stop.
    assert len(rejects) == 1
    assert rejects[0]["line_num"] == 1
    assert rejects[0]["errors"][0]["path"] == "name"
    assert rejects[0]["errors"][0]["expected"] == "COLUMN_PRESENT"


def test_stream_csv_ignore_nulls(tmp_path):
    """Ensures the ignore_nulls=True flag forces the engine to forgive missing data."""

    class RequiredContract(BaseModel):
        id: int
        name: str  # Required! No Optional[] here.

    file_path = tmp_path / "nulls.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name"])
        writer.writerow(["1", ""])  # Empty string (Null marker)

    # With default settings, it should flag the empty string as an error
    strict_rejects = list(stream_csv_contract(RequiredContract, str(file_path)))
    assert len(strict_rejects) == 1

    # With ignore_nulls=True, it should forgive it and yield nothing
    forgiving_rejects = list(
        stream_csv_contract(RequiredContract, str(file_path), ignore_nulls=True)
    )
    assert len(forgiving_rejects) == 0
