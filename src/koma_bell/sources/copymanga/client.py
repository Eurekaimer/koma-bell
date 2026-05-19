import httpx

from koma_bell.exceptions import SourceError
from koma_bell.models import ComicInfo, Subscription
from koma_bell.sources.copymanga.parser import parse_detail
from koma_bell.utils.http import make_client


class CopyMangaClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self.client = client or make_client()

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def inspect(self, subscription: Subscription) -> ComicInfo:
        try:
            response = self.client.get(subscription.url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SourceError(f"Failed to fetch comic detail: {subscription.url} ({exc})") from exc
        title, latest, updated_at = parse_detail(response.text, subscription.url)
        return ComicInfo(
            subscription_id=subscription.id,
            title=subscription.name or title,
            url=subscription.url,
            latest_chapter=latest,
            updated_at=updated_at,
        )
