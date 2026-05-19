from datetime import date, timedelta
from typing import Protocol

from koma_bell.models import CheckResult

RECENT_DAYS = 7


class Mailer(Protocol):
    def send(self, subject: str, body: str) -> None: ...


def notify_updates(mailer: Mailer, results: list[CheckResult]) -> None:
    updates = [result for result in results if result.has_update and _is_recent(result)]
    if not updates:
        return
    lines = ["发现漫画更新：", ""]
    for result in updates:
        lines.extend(_format_result(result))
    mailer.send(subject=f"koma-bell 发现 {len(updates)} 本漫画更新", body="\n".join(lines))


def send_check_preview(mailer: Mailer, results: list[CheckResult]) -> None:
    recent_results = [result for result in results if _is_recent(result)]
    lines = [f"koma-bell 最近 {RECENT_DAYS} 天更新预览：", ""]
    if not recent_results:
        lines.append(f"最近 {RECENT_DAYS} 天没有可显示的订阅更新。")
    for result in recent_results:
        lines.extend(_format_result(result))
    mailer.send(subject="koma-bell 检查结果预览", body="\n".join(lines))


def _format_result(result: CheckResult) -> list[str]:
    chapter = result.current.latest_chapter
    lines = [
        f"+ {result.current.title}",
        f"  最新章节：{chapter.title}",
    ]
    if result.current.updated_at:
        marker = " NEW" if result.current.updated_at == date.today().isoformat() else ""
        lines.append(f"  最后更新：{result.current.updated_at}{marker}")
    lines.extend(
        [
            f"  链接：{chapter.url}",
            "",
        ]
    )
    return lines


def _is_recent(result: CheckResult) -> bool:
    updated_at = result.current.updated_at
    if not updated_at:
        return True
    try:
        updated_date = date.fromisoformat(updated_at)
    except ValueError:
        return True
    return updated_date >= date.today() - timedelta(days=RECENT_DAYS)
