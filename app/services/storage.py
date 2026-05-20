"""
Simple JSON file-based storage for visit records.
"""

import json
from pathlib import Path

DATA_FILE = "data/visits.json"


def load_visits() -> list[dict]:
    """Load all visits from the JSON data file.

    Returns an empty list if the file is missing, empty,
    contains invalid JSON, or an I/O error occurs.
    """
    file_path = Path(DATA_FILE)

    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []
    except OSError:
        return []


def save_visit(visit: dict) -> dict:
    """Append a new visit dictionary to the data file and return it."""
    visits = load_visits()
    file_path = Path(DATA_FILE)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    visits.append(visit)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(visits, f, indent=2, default=str)

    return visit


if __name__ == "__main__":
    dummy = {
        "id": "test123",
        "customer_name": "Alice",
        "company": "Acme Corp",
        "visit_date": "2025-03-21",
        "topics": ["product demo", "pricing"],
        "action_items": ["send follow-up email"],
        "sentiment": "positive",
        "raw_input_type": "text",
        "created_at": "2025-03-21T14:30:00",
    }

    save_visit(dummy)
    loaded = load_visits()

    success = any(v.get("id") == "test123" for v in loaded)

    if success:
        print("Round-trip successful: visit saved and re-loaded correctly.")
    else:
        print("Round-trip failed: visit not found after loading.")
