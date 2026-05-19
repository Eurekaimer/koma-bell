from typer.testing import CliRunner

from koma_bell.cli import app
from koma_bell.models import Chapter, ComicInfo


class FakeCopyMangaClient:
    def inspect(self, subscription):
        return ComicInfo(
            subscription_id=subscription.id,
            title=subscription.name or "测试漫画",
            url=subscription.url,
            latest_chapter=Chapter("第 12 话 新的钟声", "https://www.copymanga.tv/comic/test/chapter/latest"),
        )

    def close(self):
        return None


def test_cli_check_dry_run_does_not_write_state(monkeypatch, fixtures_dir, tmp_path):
    monkeypatch.setattr("koma_bell.cli.CopyMangaClient", FakeCopyMangaClient)
    state = tmp_path / "state.json"
    state.write_text(
        (fixtures_dir / "state.old.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    before = state.read_text(encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "check",
            "--dry-run",
            "--config",
            str(fixtures_dir / "config.valid.yml"),
            "--state",
            str(state),
        ],
    )

    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert state.read_text(encoding="utf-8") == before


def test_cli_check_dry_run_can_send_preview_mail(monkeypatch, fixtures_dir, tmp_path):
    sent = {}

    class FakeMailer:
        @classmethod
        def from_env(cls):
            return cls()

        def send(self, subject, body):
            sent["subject"] = subject
            sent["body"] = body

    monkeypatch.setattr("koma_bell.cli.CopyMangaClient", FakeCopyMangaClient)
    monkeypatch.setattr("koma_bell.cli.SMTPMailer", FakeMailer)
    state = tmp_path / "state.json"
    state.write_text(
        (fixtures_dir / "state.old.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    before = state.read_text(encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "check",
            "--dry-run",
            "--send-test-mail",
            "--config",
            str(fixtures_dir / "config.valid.yml"),
            "--state",
            str(state),
        ],
    )

    assert result.exit_code == 0
    assert "preview mail sent" in result.output
    assert "第 12 话 新的钟声" in sent["body"]
    assert state.read_text(encoding="utf-8") == before
