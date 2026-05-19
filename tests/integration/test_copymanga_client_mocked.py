import httpx

from koma_bell.models import Subscription
from koma_bell.sources.copymanga.client import CopyMangaClient


def test_copymanga_client_inspect_mocked(httpx_mock, fixtures_dir):
    html = (fixtures_dir / "copymanga_detail.html").read_text(encoding="utf-8")
    httpx_mock.add_response(url="https://www.copymanga.tv/comic/test", text=html)
    client = CopyMangaClient(httpx.Client(trust_env=False))

    info = client.inspect(Subscription("test", None, "https://www.copymanga.tv/comic/test"))

    assert info.title == "测试漫画"
    assert info.latest_chapter.title == "第 12 话 新的钟声"
