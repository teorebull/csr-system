from __future__ import annotations

import csv
import json
from pathlib import Path


def read_csv_rows(csv_path: Path) -> list[dict]:
    """Read a CSV file into a list of dictionaries."""

    with Path(csv_path).open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv_rows(rows: list[dict], output_path: Path, fieldnames: list[str] | None = None) -> None:
    """Write a list of dictionaries to CSV."""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_json_dict(json_path: Path) -> dict:
    """Read a JSON file into a dictionary, or return an empty one."""

    path = Path(json_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json_dict(data: dict, json_path: Path) -> None:
    """Write a dictionary to JSON with stable formatting."""

    path = Path(json_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def rows_to_dicts(items: list[dict]) -> list[dict]:
    """Convert mixed Pydantic/dict rows into plain dictionaries."""

    return [item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in items]
