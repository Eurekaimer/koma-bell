from pathlib import Path
from typing import Any

import yaml

from koma_bell.exceptions import ConfigError
from koma_bell.models import AppConfig, RequestInterval, Subscription
from koma_bell.paths import default_config_path, default_subscriptions_path

REQUIRED_MAIL_ENV = ("MAIL_USER", "MAIL_AUTH_CODE", "MAIL_TO")
REQUIRED_ENV = REQUIRED_MAIL_ENV


def ensure_config(path: Path | None = None) -> Path:
    resolved = path or default_config_path()
    if resolved.exists():
        return resolved
    resolved.parent.mkdir(parents=True, exist_ok=True)
    save_config(
        AppConfig(subscriptions=[], subscriptions_file=default_subscriptions_path().name),
        resolved,
    )
    return resolved


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")
    if not path.is_file():
        raise ConfigError(f"Config path is not a file: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Cannot read config file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML config: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping.")

    subscriptions_file = _parse_subscriptions_file(raw.get("subscriptions_file"))
    inline_subscriptions = _parse_subscriptions(raw.get("subscriptions"))
    file_subscriptions = _load_subscriptions_file(path, subscriptions_file)
    subscriptions = _merge_subscriptions(file_subscriptions, inline_subscriptions)
    interval = _parse_interval(raw.get("request_interval_seconds"))
    first_run_notify = bool(raw.get("first_run_notify", False))
    return AppConfig(
        subscriptions=subscriptions,
        first_run_notify=first_run_notify,
        subscriptions_file=subscriptions_file,
        request_interval_seconds=interval,
    )


def save_config(config: AppConfig, path: Path) -> None:
    payload = {
        "first_run_notify": config.first_run_notify,
        "subscriptions_file": config.subscriptions_file,
        "request_interval_seconds": {
            "min": config.request_interval_seconds.min,
            "max": config.request_interval_seconds.max,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def add_subscription(path: Path, subscription: Subscription) -> AppConfig:
    config = load_config(path)
    subscriptions = [item for item in config.subscriptions if item.id != subscription.id]
    subscriptions.append(subscription)
    subscriptions.sort(key=lambda item: item.id)
    next_config = AppConfig(
        subscriptions=subscriptions,
        first_run_notify=config.first_run_notify,
        subscriptions_file=config.subscriptions_file or default_subscriptions_path().name,
        request_interval_seconds=config.request_interval_seconds,
    )
    subscriptions_path = _resolve_subscriptions_path(path, next_config.subscriptions_file)
    save_subscriptions(subscriptions_path, subscriptions)
    save_config(next_config, path)
    return next_config


def save_subscriptions(path: Path, subscriptions: list[Subscription]) -> None:
    payload = [
        {"id": item.id, "name": item.name, "url": item.url}
        for item in sorted(subscriptions, key=lambda item: item.id)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def missing_env(names: tuple[str, ...] = REQUIRED_ENV) -> list[str]:
    import os

    return [name for name in names if not os.getenv(name)]


def _parse_subscriptions(value: Any) -> list[Subscription]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError("Config subscriptions must be a list.")

    subscriptions: list[Subscription] = []
    seen: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"Subscription #{index} must be a mapping.")
        sub_id = item.get("id")
        url = item.get("url")
        name = item.get("name")
        if not isinstance(sub_id, str) or not sub_id.strip():
            raise ConfigError(f"Subscription #{index} requires a non-empty id.")
        if sub_id in seen:
            raise ConfigError(f"Duplicate subscription id: {sub_id}")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ConfigError(f"Subscription {sub_id} requires an http(s) url.")
        if name is not None and not isinstance(name, str):
            raise ConfigError(f"Subscription {sub_id} name must be a string.")
        seen.add(sub_id)
        subscriptions.append(Subscription(id=sub_id, name=name, url=url))
    return subscriptions


def _parse_subscriptions_file(value: Any) -> str | None:
    if value is None:
        return default_subscriptions_path().name
    if value is False:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("subscriptions_file must be a non-empty string or false.")
    return value


def _load_subscriptions_file(
    config_path: Path,
    subscriptions_file: str | None,
) -> list[Subscription]:
    if subscriptions_file is None:
        return []
    path = _resolve_subscriptions_path(config_path, subscriptions_file)
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Cannot read subscriptions file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid subscriptions YAML: {exc}") from exc
    return _parse_subscriptions(raw)


def _resolve_subscriptions_path(config_path: Path, subscriptions_file: str | None) -> Path:
    if subscriptions_file is None:
        return default_subscriptions_path()
    path = Path(subscriptions_file)
    if path.is_absolute():
        return path
    return config_path.parent / path


def _merge_subscriptions(
    file_subscriptions: list[Subscription],
    inline_subscriptions: list[Subscription],
) -> list[Subscription]:
    merged = {item.id: item for item in file_subscriptions}
    for item in inline_subscriptions:
        merged[item.id] = item
    return list(merged.values())


def _parse_interval(value: Any) -> RequestInterval:
    if value is None:
        return RequestInterval()
    if not isinstance(value, dict):
        raise ConfigError("request_interval_seconds must be a mapping.")
    min_seconds = int(value.get("min", 2))
    max_seconds = int(value.get("max", 5))
    if min_seconds < 0 or max_seconds < min_seconds:
        raise ConfigError("request_interval_seconds must satisfy 0 <= min <= max.")
    return RequestInterval(min=min_seconds, max=max_seconds)
