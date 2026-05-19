from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from koma_bell.exceptions import SourceError


@dataclass(frozen=True)
class ComicUrl:
    comic_id: str
    detail_url: str


def parse_comic_url(url: str) -> ComicUrl:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    try:
        comic_index = parts.index("comic")
        comic_id = parts[comic_index + 1]
    except (ValueError, IndexError) as exc:
        raise SourceError("URL must contain /comic/{comic_id}.") from exc

    if not comic_id:
        raise SourceError("Comic id is empty.")

    detail_path = "/" + "/".join(parts[: comic_index + 2])
    detail_url = urlunparse(
        (
            parsed.scheme or "https",
            parsed.netloc,
            detail_path,
            "",
            "",
            "",
        )
    )
    return ComicUrl(comic_id=comic_id, detail_url=detail_url)
