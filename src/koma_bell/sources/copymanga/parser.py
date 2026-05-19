from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from koma_bell.exceptions import SourceError
from koma_bell.models import Chapter

ACTION_TEXTS = (
    "開始閱讀",
    "开始阅读",
    "加入書架",
    "加入书架",
    "分享",
)
TITLE_SELECTORS = (
    "h1.comicParticulars-title",
    ".comicParticulars-title",
    ".comicParticulars-right h6",
    ".comicParticulars-title-right h6",
    ".comic-title",
    ".detail-info-title",
    ".fed-part-eone h1",
    "h6[title]",
    "h1",
    "title",
)
CHAPTER_SELECTORS = (
    ".comicParticulars-list a[href*='/chapter/']",
    ".chapter-list a[href*='/chapter/']",
    ".chapter-list a[href*='chapter']",
    ".comic-chapters a[href*='chapter']",
    ".detail-list a[href*='chapter']",
    "a[href*='/chapter/']",
    "a[href*='chapter']",
)
UPDATED_LABELS = (
    "最後更新：",
    "最后更新：",
    "最後更新:",
    "最后更新:",
    "更新时间：",
    "更新時間：",
)


def parse_detail(html: str, page_url: str) -> tuple[str, Chapter, str | None]:
    tree = HTMLParser(html)
    page_text = " ".join(tree.body.text(separator=" ").split()) if tree.body else ""
    title_text = _first_text(tree, ("title",))
    title = _clean_title(_first_text(tree, TITLE_SELECTORS), page_text)
    fallback_chapter_title = _extract_chapter_from_title(title_text)
    updated_at = _extract_updated_at(page_text)
    chapter = None
    for selector in CHAPTER_SELECTORS:
        nodes = tree.css(selector)
        chapter = _first_chapter(nodes, page_url, fallback_chapter_title)
        if chapter is not None:
            break
    if title is None:
        raise SourceError("Could not parse comic title.")
    if chapter is None:
        raise SourceError("Could not parse latest chapter.")

    return title, chapter, updated_at


def _first_text(tree: HTMLParser, selectors: tuple[str, ...]) -> str | None:
    for selector in selectors:
        node = tree.css_first(selector)
        if node is None:
            continue
        text = " ".join(node.text(separator=" ").split())
        if text:
            if selector == "title" and "_" in text:
                return text.split("_", 1)[0].strip()
            return text
    return None


def _first_chapter(  # type: ignore[no-untyped-def]
    nodes,
    page_url: str,
    fallback_title: str | None,
) -> Chapter | None:
    for node in nodes:
        raw_title = " ".join(node.text(separator=" ").split())
        chapter_title = _clean_chapter_title(raw_title)
        href = node.attributes.get("href")
        if not href:
            continue
        if any(text in raw_title for text in ACTION_TEXTS):
            if fallback_title:
                return Chapter(title=fallback_title, url=urljoin(page_url, href))
            continue
        if not chapter_title:
            if fallback_title:
                return Chapter(title=fallback_title, url=urljoin(page_url, href))
            continue
        return Chapter(title=chapter_title, url=urljoin(page_url, href))
    return None


def _clean_title(text: str | None, page_text: str) -> str | None:
    if not text:
        return None
    for marker in ("別名：", "别名：", "作者：", "熱度：", "最后更新：", "最後更新："):
        if marker in text:
            text = text.split(marker, 1)[0]
    text = _remove_actions(text)
    text = " ".join(text.split()).strip(" -_")
    if text and text != page_text:
        return text

    for marker in ("別名：", "别名：", "作者：", "熱度：", "最后更新：", "最後更新："):
        if marker in page_text:
            candidate = page_text.split(marker, 1)[0]
            candidate = _remove_actions(candidate)
            candidate = " ".join(candidate.split()).strip(" -_")
            if candidate:
                return candidate
    return text or None


def _clean_chapter_title(text: str) -> str:
    return _remove_actions(text).strip()


def _remove_actions(text: str) -> str:
    for action in ACTION_TEXTS:
        text = text.replace(action, " ")
    return " ".join(text.split())


def _extract_updated_at(page_text: str) -> str | None:
    for label in UPDATED_LABELS:
        if label not in page_text:
            continue
        value = page_text.split(label, 1)[1].strip()
        return value.split(" ", 1)[0].strip() or None
    return None


def _extract_chapter_from_title(text: str | None) -> str | None:
    if not text:
        return None
    parts = [item.strip() for item in text.split("-") if item.strip()]
    for part in parts:
        if part.startswith("第") and ("話" in part or "话" in part):
            return part
    for part in parts[1:]:
        if _looks_like_chapter_title(part):
            return part
    return None


def _looks_like_chapter_title(text: str) -> bool:
    ignored = (
        "連載中",
        "连载中",
        "完結",
        "完结",
        "漫画",
        "漫畫",
        "在线阅读",
        "在線閱讀",
        "拷貝漫畫",
        "拷贝漫画",
    )
    return bool(text) and not any(marker in text for marker in ignored)
