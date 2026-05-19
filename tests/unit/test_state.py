from koma_bell.models import ComicState
from koma_bell.state import StateStore


def test_state_store_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    store = StateStore(path)
    store.save(
        {
            "test": ComicState(
                title="测试漫画",
                url="https://example.test/comic",
                latest_chapter_title="第 1 话",
                latest_chapter_url="https://example.test/chapter/1",
                checked_at="2026-05-18T00:00:00+00:00",
            )
        }
    )

    loaded = store.load()

    assert loaded["test"].latest_chapter_title == "第 1 话"


def test_missing_state_is_empty(tmp_path):
    assert StateStore(tmp_path / "missing.json").load() == {}
