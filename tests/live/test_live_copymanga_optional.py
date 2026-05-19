import os

import pytest

from koma_bell.models import Subscription
from koma_bell.sources.copymanga import CopyMangaClient

pytestmark = pytest.mark.skipif(
    os.getenv("KOMA_BELL_LIVE_TEST") != "1",
    reason="live tests require KOMA_BELL_LIVE_TEST=1",
)


def test_live_copymanga_inspect():
    url = os.getenv("KOMA_BELL_LIVE_COPYMANGA_URL")
    if not url:
        pytest.skip("KOMA_BELL_LIVE_COPYMANGA_URL is not set")
    client = CopyMangaClient()
    try:
        info = client.inspect(Subscription("live", None, url))
    finally:
        client.close()
    assert info.title
    assert info.latest_chapter.title
