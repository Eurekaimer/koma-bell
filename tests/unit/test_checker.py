from koma_bell.checker import Checker
from koma_bell.models import AppConfig, Chapter, ComicInfo, ComicState, Subscription


class FakeSource:
    def inspect(self, subscription):
        return ComicInfo(
            subscription_id=subscription.id,
            title="测试漫画",
            url=subscription.url,
            latest_chapter=Chapter("第 12 话", "https://example.test/chapter/12"),
        )


def test_checker_detects_update():
    subscription = Subscription("test", "测试漫画", "https://example.test/comic")
    states = {
        "test": ComicState(
            title="测试漫画",
            url=subscription.url,
            latest_chapter_title="第 11 话",
            latest_chapter_url="https://example.test/chapter/11",
            checked_at="2026-05-17T00:00:00+00:00",
        )
    }

    results, next_states = Checker(FakeSource()).check(
        AppConfig(subscriptions=[subscription]), states, sleep_between=False
    )

    assert results[0].has_update is True
    assert next_states["test"].latest_chapter_title == "第 12 话"


def test_first_run_does_not_notify_by_default():
    subscription = Subscription("test", None, "https://example.test/comic")

    results, _ = Checker(FakeSource()).check(
        AppConfig(subscriptions=[subscription]), {}, sleep_between=False
    )

    assert results[0].is_first_run is True
    assert results[0].has_update is False
