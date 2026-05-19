import pytest

from koma_bell.config import load_config, missing_env
from koma_bell.exceptions import ConfigError


def test_load_config(fixtures_dir):
    config = load_config(fixtures_dir / "config.valid.yml")

    assert config.subscriptions[0].id == "test-comic"
    assert config.request_interval_seconds.min == 0


def test_load_config_rejects_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.yml")


def test_missing_env(monkeypatch):
    monkeypatch.delenv("MAIL_USER", raising=False)
    monkeypatch.setenv("MAIL_AUTH_CODE", "secret")

    assert missing_env(("MAIL_USER", "MAIL_AUTH_CODE")) == ["MAIL_USER"]
