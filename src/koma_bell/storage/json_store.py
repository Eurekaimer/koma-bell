import json
from pathlib import Path
from typing import Any

from koma_bell.exceptions import StateError


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StateError(f"Cannot read state file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StateError(f"Invalid JSON state: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise StateError(f"Cannot write state file: {path}") from exc
