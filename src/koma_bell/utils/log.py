SENSITIVE_KEYS = ("PASSWORD", "AUTH_CODE", "COOKIE", "TOKEN")


def redact_env_name(name: str) -> str:
    if any(key in name.upper() for key in SENSITIVE_KEYS):
        return f"{name}=<redacted>"
    return f"{name}=<set>"
