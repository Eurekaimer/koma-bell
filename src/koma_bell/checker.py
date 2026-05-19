import random
import time

from koma_bell.models import AppConfig, CheckResult, ComicState
from koma_bell.sources.base import SourceAdapter
from koma_bell.utils.time import utc_now_iso


class Checker:
    def __init__(self, source: SourceAdapter, sleep_func=time.sleep) -> None:  # type: ignore[no-untyped-def]
        self.source = source
        self.sleep_func = sleep_func

    def check(
        self,
        config: AppConfig,
        states: dict[str, ComicState],
        *,
        sleep_between: bool = True,
    ) -> tuple[list[CheckResult], dict[str, ComicState]]:
        results: list[CheckResult] = []
        next_states = dict(states)
        total = len(config.subscriptions)
        for index, subscription in enumerate(config.subscriptions):
            current = self.source.inspect(subscription)
            previous = states.get(subscription.id)
            is_first_run = previous is None
            has_changed = (
                previous is not None
                and previous.latest_chapter_url != current.latest_chapter.url
            )
            has_update = has_changed or (is_first_run and config.first_run_notify)
            results.append(
                CheckResult(
                    subscription=subscription,
                    current=current,
                    previous=previous,
                    is_first_run=is_first_run,
                    has_update=has_update,
                )
            )
            next_states[subscription.id] = ComicState(
                title=current.title,
                url=current.url,
                latest_chapter_title=current.latest_chapter.title,
                latest_chapter_url=current.latest_chapter.url,
                checked_at=utc_now_iso(),
            )
            if sleep_between and index < total - 1:
                delay = random.uniform(
                    config.request_interval_seconds.min,
                    config.request_interval_seconds.max,
                )
                self.sleep_func(delay)
        return results, next_states
