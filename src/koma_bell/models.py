from dataclasses import dataclass


@dataclass(frozen=True)
class Subscription:
    id: str
    name: str | None
    url: str


@dataclass(frozen=True)
class RequestInterval:
    min: int = 2
    max: int = 5


@dataclass(frozen=True)
class AppConfig:
    subscriptions: list[Subscription]
    first_run_notify: bool = False
    subscriptions_file: str | None = "subscriptions.yml"
    request_interval_seconds: RequestInterval = RequestInterval()


@dataclass(frozen=True)
class Chapter:
    title: str
    url: str


@dataclass(frozen=True)
class ComicInfo:
    subscription_id: str
    title: str
    url: str
    latest_chapter: Chapter
    updated_at: str | None = None


@dataclass(frozen=True)
class ComicState:
    title: str
    url: str
    latest_chapter_title: str
    latest_chapter_url: str
    checked_at: str


@dataclass(frozen=True)
class CheckResult:
    subscription: Subscription
    current: ComicInfo
    previous: ComicState | None
    is_first_run: bool
    has_update: bool
