import subprocess
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from koma_bell.checker import Checker
from koma_bell.config import add_subscription, ensure_config, load_config, save_subscriptions
from koma_bell.exceptions import KomaBellError
from koma_bell.mail.smtp import SMTPMailer
from koma_bell.models import CheckResult, Subscription
from koma_bell.notifier import notify_updates, send_check_preview
from koma_bell.paths import (
    default_config_path,
    default_secrets_path,
    default_state_path,
    default_subscriptions_path,
)
from koma_bell.secrets import (
    MailCredentials,
    get_mail_credentials,
    missing_secret_names,
    save_secrets,
)
from koma_bell.sources.copymanga import CopyMangaClient
from koma_bell.sources.copymanga.url import parse_comic_url
from koma_bell.state import StateStore

app = typer.Typer(invoke_without_command=True, help="Lightweight manga update notifier.")
console = Console()
DEFAULT_CONFIG_PATH = Path("config.yml") if Path("config.yml").exists() else default_config_path()
DEFAULT_STATE_PATH = default_state_path()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Start the interactive menu when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        run_menu()


@app.command("configure")
def configure() -> None:
    """Open the interactive local configuration wizard."""
    _configure_menu()


@app.command("add")
def add(
    url: Annotated[str, typer.Argument(metavar="URL")],
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    name: Annotated[str | None, typer.Option("--name", help="Comic name fallback.")] = None,
) -> None:
    """Inspect a comic URL and add it to config.yml automatically."""
    resolved_config = ensure_config(config)
    try:
        comic_url = parse_comic_url(url)
    except KomaBellError as exc:
        _fail(str(exc))
    info = None
    comic_name = name
    try:
        info = _inspect(comic_url.detail_url)
        comic_name = info.title
        console.print("[green]OK[/green] URL metadata parsed.")
        _print_inspect_result(info)
    except KomaBellError as exc:
        console.print(f"[yellow]URL metadata parse failed:[/yellow] {exc}")
        console.print("[yellow]将使用 URL 直接添加订阅。之后检查更新时仍会再次尝试访问。[/yellow]")
    if not comic_name:
        comic_name = typer.prompt("漫画名")
    sub_id = comic_url.comic_id
    add_subscription(
        resolved_config,
        Subscription(id=sub_id, name=comic_name, url=comic_url.detail_url),
    )
    console.print(f"[green]OK[/green] added subscription `{sub_id}` to {resolved_config}")
    console.print(f"订阅 URL: {comic_url.detail_url}")


@app.command("config-check")
def config_check(
    config: Annotated[Path, typer.Option("--config", exists=False)] = DEFAULT_CONFIG_PATH,
) -> None:
    """Check config readability and local credentials."""
    try:
        ensure_config(config)
        cfg = load_config(config)
        missing = missing_secret_names()
    except KomaBellError as exc:
        _fail(str(exc))
    if missing:
        _fail("Missing local credentials: " + ", ".join(missing))
    console.print(
        f"[green]OK[/green] config readable, {len(cfg.subscriptions)} subscriptions loaded."
    )
    _print_paths(config)


@app.command("inspect")
def inspect_url(url: Annotated[str, typer.Argument(metavar="URL")]) -> None:
    """Inspect one CopyManga comic URL."""
    try:
        info = _inspect(url)
    except KomaBellError as exc:
        _fail(str(exc))
    _print_inspect_result(info)


@app.command("paths")
def paths() -> None:
    """Show local config, secrets, and state file locations."""
    _print_paths(DEFAULT_CONFIG_PATH)


@app.command("subscriptions")
def subscriptions(
    config: Annotated[Path, typer.Option("--config", exists=False)] = DEFAULT_CONFIG_PATH,
    urls_only: Annotated[
        bool,
        typer.Option("--urls-only", help="Print only subscription URLs."),
    ] = False,
) -> None:
    """Show all configured subscription URLs."""
    try:
        ensure_config(config)
        cfg = load_config(config)
    except KomaBellError as exc:
        _fail(str(exc))
    _print_subscriptions(cfg.subscriptions, urls_only=urls_only)


@app.command("banner")
def banner() -> None:
    """Show the koma-bell banner."""
    _print_banner()


def _inspect(url: str):
    client = CopyMangaClient()
    try:
        info = client.inspect(Subscription(id="inspect", name=None, url=url))
    finally:
        client.close()
    return info


def _print_inspect_result(info) -> None:  # type: ignore[no-untyped-def]
    table = Table(title="Comic")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Name", info.title)
    table.add_row("Latest chapter", info.latest_chapter.title)
    table.add_row("Chapter URL", info.latest_chapter.url)
    console.print(table)


@app.command("check")
def check(
    config: Annotated[Path, typer.Option("--config", exists=False)] = DEFAULT_CONFIG_PATH,
    state: Annotated[Path, typer.Option("--state")] = DEFAULT_STATE_PATH,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Do not send mail or write state.")
    ] = False,
    send_test_mail: Annotated[
        bool,
        typer.Option(
            "--send-test-mail",
            help="Send a preview mail with current latest chapters. State is not written.",
        ),
    ] = False,
) -> None:
    """Check all subscriptions, notify updates, and update state."""
    try:
        ensure_config(config)
        cfg = load_config(config)
        store = StateStore(state)
        states = store.load()
        client = CopyMangaClient()
        try:
            results, next_states = Checker(client).check(cfg, states, sleep_between=not dry_run)
        finally:
            client.close()
        _print_results(results)
        if send_test_mail:
            send_check_preview(SMTPMailer.from_env(), results)
            console.print("[green]OK[/green] preview mail sent.")
            if dry_run:
                console.print("[yellow]dry-run[/yellow] state not written.")
                return
        if dry_run:
            console.print("[yellow]dry-run[/yellow] no mail sent and state not written.")
            return
        notify_updates(SMTPMailer.from_env(), results)
        store.save(next_states)
        console.print(f"[green]OK[/green] state updated: {state}")
    except KomaBellError as exc:
        _fail(str(exc))


@app.command("mail-test")
def mail_test(
    config: Annotated[Path, typer.Option("--config", exists=False)] = DEFAULT_CONFIG_PATH,
) -> None:
    """Send a mail test message."""
    try:
        ensure_config(config)
        load_config(config)
        SMTPMailer.from_env().send(
            "koma-bell 测试邮件",
            "这是一封 koma-bell 测试邮件。若你收到了它，说明 QQ 邮箱 SMTP 配置可用。",
        )
    except KomaBellError as exc:
        _fail(str(exc))
    console.print("[green]OK[/green] test mail sent.")


@app.command("mail-check")
def mail_check() -> None:
    """Diagnose mail settings without printing the auth code."""
    try:
        credentials = get_mail_credentials()
        console.print("SMTP: smtp.qq.com:465 SSL")
        console.print(f"From: {credentials.user}")
        console.print(f"To: {credentials.to}")
        console.print(f"Auth code length: {len(credentials.auth_code)}")
        SMTPMailer.from_env().send(
            "koma-bell 邮箱诊断",
            "这是一封 koma-bell 邮箱诊断邮件。收到它表示 SMTP 登录和发送都成功。",
        )
    except KomaBellError as exc:
        _fail(str(exc))
    console.print("[green]OK[/green] diagnostic mail sent.")


@app.command("github-setup")
def github_setup(
    repo: Annotated[str, typer.Option("--repo", help="GitHub repo, for example owner/name.")],
    config: Annotated[Path, typer.Option("--config", exists=False)] = DEFAULT_CONFIG_PATH,
) -> None:
    """Write local config and mail settings to GitHub Actions Secrets using gh."""
    if "/" not in repo:
        _fail("Repo must look like owner/name.")
    try:
        ensure_config(config)
        cfg = load_config(config)
        credentials = get_mail_credentials()
        subscriptions_path = _subscriptions_path_for_config(config, cfg.subscriptions_file)
        save_subscriptions(subscriptions_path, cfg.subscriptions)
        config_text = config.read_text(encoding="utf-8")
        subscriptions_text = subscriptions_path.read_text(encoding="utf-8")
        secrets = {
            "KOMA_BELL_CONFIG_YML": config_text,
            "KOMA_BELL_SUBSCRIPTIONS_YML": subscriptions_text,
            "MAIL_USER": credentials.user,
            "MAIL_AUTH_CODE": credentials.auth_code,
            "MAIL_TO": credentials.to,
        }
        for name, value in secrets.items():
            _set_github_secret(repo, name, value)
            console.print(f"[green]OK[/green] set GitHub secret `{name}`")
    except KomaBellError as exc:
        _fail(str(exc))
    console.print("[green]OK[/green] GitHub Actions secrets configured.")


@app.command("state-show")
def state_show(state: Annotated[Path, typer.Option("--state")] = DEFAULT_STATE_PATH) -> None:
    """Show saved comic state."""
    try:
        states = StateStore(state).load()
    except KomaBellError as exc:
        _fail(str(exc))
    table = Table(title="State")
    table.add_column("ID")
    table.add_column("Comic")
    table.add_column("Latest")
    table.add_column("Checked At")
    for key, value in sorted(states.items()):
        table.add_row(key, value.title, value.latest_chapter_title, value.checked_at)
    console.print(table)


def run_menu() -> None:
    _print_banner()
    _print_paths(DEFAULT_CONFIG_PATH)
    while True:
        console.print()
        console.print("1. 配置邮箱")
        console.print("2. 添加订阅")
        console.print("3. 查看订阅 URL")
        console.print("4. 立即检查，有最近更新就发邮件")
        console.print("5. 发送一封预览测试邮件")
        console.print("6. 同步配置到 GitHub Actions")
        console.print("7. 查看本机文件位置")
        console.print("0. 退出")
        choice = typer.prompt("请选择", default="0")
        if choice == "1":
            _configure_mail()
        elif choice == "2":
            _menu_add_subscription()
        elif choice == "3":
            subscriptions(config=DEFAULT_CONFIG_PATH)
        elif choice == "4":
            check(config=DEFAULT_CONFIG_PATH, state=DEFAULT_STATE_PATH, dry_run=False)
        elif choice == "5":
            check(
                config=DEFAULT_CONFIG_PATH,
                state=DEFAULT_STATE_PATH,
                dry_run=True,
                send_test_mail=True,
            )
        elif choice == "6":
            repo = typer.prompt("GitHub 仓库（owner/name）")
            github_setup(repo=repo, config=DEFAULT_CONFIG_PATH)
        elif choice == "7":
            _print_paths(DEFAULT_CONFIG_PATH)
        elif choice == "0":
            raise typer.Exit()
        else:
            console.print("[yellow]请输入 0 到 7。[/yellow]")


def _configure_menu() -> None:
    _print_banner()
    _print_paths(DEFAULT_CONFIG_PATH)
    _configure_mail()


def _configure_mail() -> None:
    user = typer.prompt("邮箱地址")
    auth_code = typer.prompt("邮箱 SMTP 授权码", hide_input=True)
    to = typer.prompt("接收提醒的邮箱（直接回车=发给自己）", default=user)
    path = save_secrets(mail=MailCredentials(user=user, auth_code=auth_code, to=to))
    console.print(f"[green]OK[/green] saved mail settings to {path}")
    if typer.confirm("是否立即发送一封测试邮件？", default=True):
        try:
            SMTPMailer.from_env().send("koma-bell 测试邮件", "这是一封 koma-bell 测试邮件。")
        except KomaBellError as exc:
            console.print(f"[red]测试邮件发送失败：[/red]{exc}")
            console.print("[yellow]邮箱配置已保存，你可以重新选择 1 修改。[/yellow]")
        else:
            console.print("[green]测试邮件发送成功。[/green]")


def _menu_add_subscription() -> None:
    url = typer.prompt("漫画详情页 URL")
    try:
        comic_url = parse_comic_url(url)
    except KomaBellError as exc:
        _fail(str(exc))
    info = None
    try:
        info = _inspect(comic_url.detail_url)
    except KomaBellError as exc:
        console.print(f"[yellow]URL metadata parse failed:[/yellow] {exc}")
        console.print("[yellow]你仍然可以手动输入漫画名，把 URL 加入订阅。[/yellow]")
        sub_id = typer.prompt("订阅 ID", default=comic_url.comic_id)
        name = typer.prompt("漫画名")
    else:
        sub_id = typer.prompt("订阅 ID", default=comic_url.comic_id)
        name = typer.prompt("漫画名", default=info.title)
        _print_inspect_result(info)
    config = ensure_config(DEFAULT_CONFIG_PATH)
    add_subscription(config, Subscription(id=sub_id, name=name, url=comic_url.detail_url))
    console.print(f"[green]OK[/green] added `{name}` to {config}")
    console.print(f"订阅 URL: {comic_url.detail_url}")


def _print_banner() -> None:
    lines = [
        r"K     K   OOOOO   M     M     A      BBBB    EEEEE   L       L",
        r"K   K    O     O  MM   MM    A A     B   B   E       L       L",
        r"K K      O     O  M M M M   AAAAA    BBBB    EEEE    L       L",
        r"K   K    O     O  M  M  M  A     A   B   B   E       L       L",
        r"K     K   OOOOO   M     M  A     A   BBBB    EEEEE   LLLLL   LLLLL",
    ]
    content_width = max(len(line) for line in lines)
    width = min(max(content_width + 8, 80), console.width)
    inner_width = width - 2
    console.print()
    console.print("#" * width, style="bold")
    console.print(("#" + " " * inner_width + "#"), style="bold")
    for line in lines:
        console.print("#" + line.center(inner_width) + "#", style="bold")
    console.print(("#" + " " * inner_width + "#"), style="bold")
    console.print("#" + "Manga update notifier".center(inner_width) + "#", style="bold")
    console.print(("#" + " " * inner_width + "#"), style="bold")
    console.print("#" * width, style="bold")


def _print_paths(config: Path) -> None:
    try:
        cfg = load_config(config)
        subscriptions_path = _subscriptions_path_for_config(config, cfg.subscriptions_file)
    except KomaBellError:
        subscriptions_path = default_subscriptions_path()
    table = Table(title="Local Files")
    table.add_column("Type")
    table.add_column("Path")
    table.add_row("config", str(config))
    table.add_row("subscriptions", str(subscriptions_path))
    table.add_row("secrets", str(default_secrets_path()))
    table.add_row("state", str(default_state_path()))
    console.print(table)


def _subscriptions_path_for_config(config: Path, subscriptions_file: str | None) -> Path:
    if subscriptions_file is None:
        return default_subscriptions_path()
    path = Path(subscriptions_file)
    if path.is_absolute():
        return path
    return config.parent / path


def _print_subscriptions(items: list[Subscription], *, urls_only: bool = False) -> None:
    if not items:
        console.print("[yellow]还没有订阅。[/yellow]")
        return
    if urls_only:
        for item in sorted(items, key=lambda value: value.id):
            console.print(item.url)
        return
    table = Table(title="Subscriptions")
    table.add_column("ID")
    table.add_column("Comic")
    table.add_column("URL")
    for item in sorted(items, key=lambda value: value.id):
        table.add_row(item.id, item.name or "", item.url)
    console.print(table)


def _set_github_secret(repo: str, name: str, value: str) -> None:
    try:
        subprocess.run(
            ["gh", "secret", "set", name, "--repo", repo, "--body", value],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise KomaBellError("GitHub CLI `gh` is not installed or not on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise KomaBellError(f"Failed to set GitHub secret `{name}`: {message}") from exc


def _print_results(results: list[CheckResult]) -> None:
    table = Table(title="Check Results")
    table.add_column("ID")
    table.add_column("Comic")
    table.add_column("Latest")
    table.add_column("Status")
    for result in results:
        if result.is_first_run and not result.has_update:
            status = "initialized"
        elif result.has_update:
            status = "updated"
        else:
            status = "unchanged"
        table.add_row(
            result.subscription.id,
            result.current.title,
            result.current.latest_chapter.title,
            status,
        )
    console.print(table)


def _fail(message: str) -> NoReturn:
    console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(1)
