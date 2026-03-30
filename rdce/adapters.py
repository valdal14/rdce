import csv
from typing import Any

from pydantic import BaseModel

from .extractor import extract_schema


def enforce_csv_structure(
    contract: type[BaseModel], file_path: str, **kwargs: Any
) -> list[dict[str, str]]:
    """
    Validates a CSV file's header against a Pydantic contract to detect schema drift.

    This adapter opens a flat file, reads only the first row (the header), and
    cross-references the column names against the keys defined in the Pydantic schema.
    It does not validate data types or row values, making it extremely fast for
    detecting dropped or renamed columns in large data pipelines.

    Args:
        contract (type[BaseModel]): The Pydantic model representing the expected schema.
        file_path (str): The absolute or relative path to the CSV file.
        **kwargs (Any): Additional keyword arguments (e.g., delimiter=";", quotechar="|")
            to pass directly to the underlying `csv.reader`.

    Returns:
        list[dict[str, str]]: A list of validation errors. Returns an empty list if
            all schema keys are present in the CSV header.
    """
    schema = extract_schema(contract)
    errors = []

    # Always open CSVs with newline="" per Python documentation
    with open(file_path, mode="r", newline="") as csv_file:
        # Pass any extra kwargs (like delimiter) directly to the reader
        reader = csv.reader(csv_file, **kwargs)

        try:
            # Grab the very first row (the header) using next()
            header = next(reader)
        except StopIteration:
            # Handle the edge case of a completely empty file
            header = []

        # Cross-reference the schema keys against the CSV header
        for key in schema.keys():
            if key not in header:
                errors.append({"path": key, "expected": "COLUMN_PRESENT", "actual": "MISSING"})

    return errors
