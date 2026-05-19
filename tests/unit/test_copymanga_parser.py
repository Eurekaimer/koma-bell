from koma_bell.sources.copymanga.parser import parse_detail


def test_parse_copymanga_detail(fixtures_dir):
    html = (fixtures_dir / "copymanga_detail.html").read_text(encoding="utf-8")

    title, chapter, updated_at = parse_detail(html, "https://www.copymanga.tv/comic/test")

    assert title == "测试漫画"
    assert chapter.title == "第 12 话 新的钟声"
    assert chapter.url == "https://www.copymanga.tv/comic/test/chapter/latest"
    assert updated_at == "2026-05-13"


def test_parse_start_reading_link_with_title_fallback():
    html = """
    <html>
      <head><title>向笨蛋告白-向笨蛋告白漫畫-第11.2話-連載中</title></head>
      <body>
        <h6 title="向笨蛋告白">向笨蛋告白</h6>
        <span class="comicParticulars-sigezi">最後更新：</span>2026-05-19
        <a href="/comic/xiangbendangaobai/chapter/latest">開始閱讀</a>
      </body>
    </html>
    """

    title, chapter, updated_at = parse_detail(html, "https://www.mangacopy.com/comic/xiangbendangaobai")

    assert title == "向笨蛋告白"
    assert chapter.title == "第11.2話"
    assert chapter.url == "https://www.mangacopy.com/comic/xiangbendangaobai/chapter/latest"
    assert updated_at == "2026-05-19"


def test_parse_start_reading_link_with_named_chapter_fallback():
    html = """
    <html>
      <head><title>想吃掉我的非人少女-想吃掉我的非人少女漫畫-鱼儿要上钩了-連載中</title></head>
      <body>
        <h6 title="想吃掉我的非人少女">想吃掉我的非人少女</h6>
        <span class="comicParticulars-sigezi">最後更新：</span>
        <span class="comicParticulars-right-txt">2026-05-15</span>
        <a href="/comic/xiangchidiaowodefeirenshaonv/chapter/latest">開始閱讀</a>
      </body>
    </html>
    """

    title, chapter, updated_at = parse_detail(
        html,
        "https://www.mangacopy.com/comic/xiangchidiaowodefeirenshaonv",
    )

    assert title == "想吃掉我的非人少女"
    assert chapter.title == "鱼儿要上钩了"
    assert chapter.url == "https://www.mangacopy.com/comic/xiangchidiaowodefeirenshaonv/chapter/latest"
    assert updated_at == "2026-05-15"
