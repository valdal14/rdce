import csv
from typing import Any, Generator

from pydantic import BaseModel

from .error_factory import build_error
from .extractor import extract_schema


def enforce_csv_structure(
    contract: type[BaseModel], file_path: str, encoding: str | None = None, **kwargs: Any
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
        encoding (str | None): The encoding used to open the file (e.g., "utf-8").
        **kwargs (Any): Additional keyword arguments (e.g., delimiter=";", quotechar="|")
            to pass directly to the underlying `csv.reader`.

    Returns:
        list[dict[str, str]]: A list of validation errors. Returns an empty list if
            all schema keys are present in the CSV header.
    """
    schema = extract_schema(contract)
    errors = []

    # Always open CSVs with newline="" per Python documentation
    # Pass encoding to open(), let kwargs (like delimiter) go to the reader
    with open(file_path, mode="r", newline="", encoding=encoding) as csv_file:
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
                errors.append(build_error(key, "COLUMN_PRESENT", "MISSING"))

    return errors


def stream_csv_contract(
    contract: type[BaseModel],
    file_path: str,
    null_markers: list[str] | None = None,
    ignore_nulls: bool = False,
    encoding: str | None = None,
    **kwargs: Any,
) -> Generator[dict[str, Any], None, None]:
    """
    Streams a CSV file row-by-row, validating data types against a Pydantic schema.
    Yields a dictionary for every row that fails validation, allowing the developer
    to route bad data without loading the entire file into memory.

    Args:
        contract (type[BaseModel]): The expected schema.
        file_path (str): Path to the CSV file.
        null_markers (list[str]): Strings that represent NULL in this CSV (e.g., "", "NaN").
        ignore_nulls (bool): If True, forgives all null markers regardless of schema.
        encoding (str | None): The encoding used to open the file (e.g., "utf-8-sig").
        **kwargs: Passed directly to `csv.DictReader` (e.g., delimiter=";").

    Yields:
        dict: A payload containing `line_num`, the `raw_row` dictionary, and `errors`.
    """
    if null_markers is None:
        null_markers = ["", "NaN", "\\N"]

    schema = extract_schema(contract)

    # Fast-Fail Structural Check (Pass encoding down!)
    structural_errors = enforce_csv_structure(contract, file_path, encoding=encoding, **kwargs)
    if structural_errors:
        yield {"line_num": 1, "raw_row": {}, "errors": structural_errors}
        # Abort the stream completely!
        return

    # Row-by-Row Coercion Stream (Pass encoding down!)
    with open(file_path, mode="r", newline="", encoding=encoding) as csv_file:
        reader = csv.DictReader(csv_file, **kwargs)

        # start=2 because line 1 is the header
        for line_index, row in enumerate(reader, start=2):
            row_errors = []

            for key, expected_type in schema.items():
                value = row.get(key)

                # Missing column entirely (Handled by structural check, but safe to skip)
                if value is None:
                    continue

                # Null Handling
                if value in null_markers:
                    if ignore_nulls:
                        continue
                    if isinstance(expected_type, tuple) and "NoneType" in expected_type:
                        continue

                    row_errors.append(build_error(key, str(expected_type), "NULL"))
                    continue

                # Type Coercion
                # Unwrap tuples (e.g., ("int", "NoneType")) to find the core type
                target_types = (
                    expected_type if isinstance(expected_type, tuple) else [expected_type]
                )
                success = False

                for t in target_types:
                    if t == "NoneType":
                        continue
                    if t == "str":
                        success = True
                        break
                    elif t == "int":
                        try:
                            int(value)
                            success = True
                            break
                        except ValueError:
                            pass
                    elif t == "float":
                        try:
                            float(value)
                            success = True
                            break
                        except ValueError:
                            pass
                    elif t == "bool":
                        # Handle CSV boolean text flags natively
                        if value.lower() in {"true", "false", "1", "0", "yes", "no", "y", "n"}:
                            success = True
                            break

                # If we tried all allowed types and none of them worked...
                if not success:
                    row_errors.append(build_error(key, str(expected_type), "str"))

            # If this row had any violations, yield it to the developer!
            if row_errors:
                yield {"line_num": line_index, "raw_row": dict(row), "errors": row_errors}
