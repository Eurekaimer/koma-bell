import os

import httpx

DEFAULT_HEADERS = {
    "User-Agent": "koma-bell/0.1 (+https://github.com/) low-frequency personal notifier",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}


def make_client() -> httpx.Client:
    return httpx.Client(
        headers=DEFAULT_HEADERS,
        timeout=httpx.Timeout(20.0),
        follow_redirects=True,
        trust_env=_trust_env(),
    )


def _trust_env() -> bool:
    value = os.getenv("KOMA_BELL_TRUST_ENV", "1").lower()
    return value not in {"0", "false", "no", "off"}
