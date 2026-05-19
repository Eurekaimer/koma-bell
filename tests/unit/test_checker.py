from datetime import date, timedelta

from koma_bell.checker import Checker
from koma_bell.models import AppConfig, Chapter, ComicInfo, ComicState, Subscription


class FakeSource:
    def __init__(self, updated_at: str | None = None):
        self.updated_at = updated_at

    def inspect(self, subscription):
        return ComicInfo(
            subscription_id=subscription.id,
            title="测试漫画",
            url=subscription.url,
            latest_chapter=Chapter("第 12 话", "https://example.test/chapter/12"),
            updated_at=self.updated_at,
        )


def test_checker_notifies_recent_updated_at_independent_of_state():
    subscription = Subscription("test", "测试漫画", "https://example.test/comic")
    recent_date = (date.today() - timedelta(days=1)).isoformat()
    states = {
        "test": ComicState(
            title="测试漫画",
            url=subscription.url,
            latest_chapter_title="第 12 话",
            latest_chapter_url="https://example.test/chapter/12",
            checked_at="2026-05-17T00:00:00+00:00",
        )
    }

    results, _ = Checker(FakeSource(updated_at=recent_date)).check(
        AppConfig(subscriptions=[subscription]), states, sleep_between=False
    )

    assert results[0].has_update is True


def test_checker_ignores_old_updated_at_even_when_chapter_changed():
    subscription = Subscription("test", "测试漫画", "https://example.test/comic")
    old_date = (date.today() - timedelta(days=8)).isoformat()
    states = {
        "test": ComicState(
            title="测试漫画",
            url=subscription.url,
            latest_chapter_title="第 11 话",
            latest_chapter_url="https://example.test/chapter/11",
            checked_at="2026-05-17T00:00:00+00:00",
        )
    }

    results, next_states = Checker(FakeSource(updated_at=old_date)).check(
        AppConfig(subscriptions=[subscription]), states, sleep_between=False
    )

    assert results[0].has_update is False
    assert next_states["test"].latest_chapter_title == "第 12 话"


def test_first_run_without_updated_at_does_not_notify():
    subscription = Subscription("test", None, "https://example.test/comic")

    results, _ = Checker(FakeSource()).check(
        AppConfig(subscriptions=[subscription]), {}, sleep_between=False
    )

    assert results[0].is_first_run is True
    assert results[0].has_update is False
