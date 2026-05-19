import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from koma_bell.exceptions import ConfigError
from koma_bell.paths import default_secrets_path

MAIL_ENV_NAMES = ("MAIL_USER", "MAIL_AUTH_CODE", "MAIL_TO")


@dataclass(frozen=True)
class MailCredentials:
    user: str
    auth_code: str
    to: str


def load_secrets(path: Path | None = None) -> dict[str, Any]:
    resolved = path or default_secrets_path()
    if not resolved.exists():
        return {}
    try:
        raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Cannot read secrets file: {resolved}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid secrets YAML: {exc}") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError("Secrets root must be a mapping.")
    return raw


def save_secrets(
    *,
    mail: MailCredentials | None = None,
    path: Path | None = None,
) -> Path:
    resolved = path or default_secrets_path()
    data = load_secrets(resolved)
    if mail is not None:
        data["mail"] = {
            "user": mail.user,
            "auth_code": mail.auth_code,
            "to": mail.to,
        }
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    resolved.chmod(0o600)
    return resolved


def get_mail_credentials(path: Path | None = None) -> MailCredentials:
    env_user, env_auth_code, env_to = _mail_env_values(MAIL_ENV_NAMES)
    if env_user and env_auth_code and env_to:
        return MailCredentials(
            user=env_user.strip(),
            auth_code=_normalize_auth_code(env_auth_code),
            to=env_to.strip(),
        )

    data = load_secrets(path)
    raw = data.get("mail")
    if isinstance(raw, dict):
        user = raw.get("user")
        auth_code = raw.get("auth_code")
        to = raw.get("to")
        if (
            isinstance(user, str)
            and isinstance(auth_code, str)
            and isinstance(to, str)
            and user
            and auth_code
            and to
        ):
            return MailCredentials(
                user=user.strip(),
                auth_code=_normalize_auth_code(auth_code),
                to=to.strip(),
            )
    raise ConfigError("Mail credentials are not configured. Run `koma-bell configure` first.")


def missing_secret_names(
    path: Path | None = None,
    *,
    include_mail: bool = True,
) -> list[str]:
    missing: list[str] = []
    if include_mail:
        try:
            get_mail_credentials(path)
        except ConfigError:
            missing.extend(["mail.user", "mail.auth_code", "mail.to"])
    return missing


def _mail_env_values(names: tuple[str, str, str]) -> tuple[str | None, str | None, str | None]:
    return os.getenv(names[0]), os.getenv(names[1]), os.getenv(names[2])


def _normalize_auth_code(value: str) -> str:
    return "".join(value.split())
