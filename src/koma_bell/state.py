from pathlib import Path
from typing import Any

from koma_bell.exceptions import StateError
from koma_bell.models import ComicState
from koma_bell.storage.json_store import read_json, write_json

STATE_VERSION = 1


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, ComicState]:
        if not self.path.exists():
            return {}
        raw = read_json(self.path)
        if not isinstance(raw, dict):
            raise StateError("State root must be a mapping.")
        comics = raw.get("comics", {})
        if not isinstance(comics, dict):
            raise StateError("State comics must be a mapping.")
        return {str(key): _state_from_dict(value) for key, value in comics.items()}

    def save(self, states: dict[str, ComicState]) -> None:
        payload = {
            "version": STATE_VERSION,
            "comics": {key: _state_to_dict(value) for key, value in sorted(states.items())},
        }
        write_json(self.path, payload)


def _state_from_dict(value: Any) -> ComicState:
    if not isinstance(value, dict):
        raise StateError("Each comic state must be a mapping.")
    try:
        return ComicState(
            title=str(value["title"]),
            url=str(value["url"]),
            latest_chapter_title=str(value["latest_chapter_title"]),
            latest_chapter_url=str(value["latest_chapter_url"]),
            checked_at=str(value["checked_at"]),
        )
    except KeyError as exc:
        raise StateError(f"Missing state field: {exc.args[0]}") from exc


def _state_to_dict(state: ComicState) -> dict[str, str]:
    return {
        "title": state.title,
        "url": state.url,
        "latest_chapter_title": state.latest_chapter_title,
        "latest_chapter_url": state.latest_chapter_url,
        "checked_at": state.checked_at,
    }
