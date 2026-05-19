from typing import Protocol

from koma_bell.models import ComicInfo, Subscription


class SourceAdapter(Protocol):
    def inspect(self, subscription: Subscription) -> ComicInfo: ...
