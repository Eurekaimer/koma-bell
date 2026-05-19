from koma_bell.sources.copymanga.url import parse_comic_url


def test_parse_comic_detail_url():
    parsed = parse_comic_url("https://www.mangacopy.com/comic/xiangbendangaobai")

    assert parsed.comic_id == "xiangbendangaobai"
    assert parsed.detail_url == "https://www.mangacopy.com/comic/xiangbendangaobai"


def test_parse_chapter_url_to_comic_url():
    parsed = parse_comic_url(
        "https://www.mangacopy.com/comic/xiangbendangaobai/"
        "chapter/6fcd320b-2d0a-11f1-8312-fa163e02432f"
    )

    assert parsed.comic_id == "xiangbendangaobai"
    assert parsed.detail_url == "https://www.mangacopy.com/comic/xiangbendangaobai"
