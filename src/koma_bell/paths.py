import os
from pathlib import Path

APP_NAME = "koma-bell"


def user_config_dir() -> Path:
    base = os.getenv("XDG_CONFIG_HOME")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def user_state_dir() -> Path:
    base = os.getenv("XDG_STATE_HOME")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".local" / "state" / APP_NAME


def default_config_path() -> Path:
    return user_config_dir() / "config.yml"


def default_subscriptions_path() -> Path:
    return user_config_dir() / "subscriptions.yml"


def default_secrets_path() -> Path:
    return user_config_dir() / "secrets.yml"


def default_state_path() -> Path:
    return user_state_dir() / "state.json"
