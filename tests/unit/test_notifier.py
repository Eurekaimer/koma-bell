from datetime import date, timedelta

from koma_bell.models import Chapter, CheckResult, ComicInfo, ComicState, Subscription
from koma_bell.notifier import notify_updates, send_check_preview


class FakeMailer:
    def __init__(self):
        self.subject = ""
        self.body = ""
        self.send_count = 0

    def send(self, subject, body):
        self.send_count += 1
        self.subject = subject
        self.body = body


def test_preview_mail_is_concise():
    mailer = FakeMailer()
    updated_at = (date.today() - timedelta(days=2)).isoformat()
    result = CheckResult(
        subscription=Subscription("test", "向笨蛋告白", "https://example.test/comic/test"),
        current=ComicInfo(
            subscription_id="test",
            title="向笨蛋告白",
            url="https://example.test/comic/test",
            latest_chapter=Chapter("第 10.1 话", "https://example.test/chapter/latest"),
            updated_at=updated_at,
        ),
        previous=None,
        is_first_run=True,
        has_update=False,
    )

    send_check_preview(mailer, [result])

    assert "+ 向笨蛋告白" in mailer.body
    assert "最新章节：第 10.1 话" in mailer.body
    assert f"最后更新：{updated_at}" in mailer.body
    assert "链接：https://example.test/chapter/latest" in mailer.body
    assert "状态：" not in mailer.body
    assert "题材" not in mailer.body
    assert "热度" not in mailer.body


def test_preview_mail_filters_old_updates():
    mailer = FakeMailer()
    old_date = (date.today() - timedelta(days=8)).isoformat()
    result = CheckResult(
        subscription=Subscription("test", "旧漫画", "https://example.test/comic/test"),
        current=ComicInfo(
            subscription_id="test",
            title="旧漫画",
            url="https://example.test/comic/test",
            latest_chapter=Chapter("第 1 话", "https://example.test/chapter/latest"),
            updated_at=old_date,
        ),
        previous=None,
        is_first_run=True,
        has_update=False,
    )

    send_check_preview(mailer, [result])

    assert "+ 旧漫画" not in mailer.body
    assert "最近 7 天没有可显示的订阅更新" in mailer.body


def test_update_mail_filters_old_updates():
    mailer = FakeMailer()
    old_date = (date.today() - timedelta(days=8)).isoformat()
    result = CheckResult(
        subscription=Subscription("test", "旧漫画", "https://example.test/comic/test"),
        current=ComicInfo(
            subscription_id="test",
            title="旧漫画",
            url="https://example.test/comic/test",
            latest_chapter=Chapter("第 1 话", "https://example.test/chapter/latest"),
            updated_at=old_date,
        ),
        previous=ComicState(
            title="旧漫画",
            url="https://example.test/comic/test",
            latest_chapter_title="第 0 话",
            latest_chapter_url="https://example.test/chapter/old",
            checked_at="2026-05-01T00:00:00+08:00",
        ),
        is_first_run=False,
        has_update=True,
    )

    notify_updates(mailer, [result])

    assert mailer.send_count == 0
