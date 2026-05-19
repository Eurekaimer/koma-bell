import smtplib
from collections.abc import Callable
from email.message import EmailMessage
from smtplib import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPException,
    SMTPRecipientsRefused,
    SMTPResponseException,
    SMTPSenderRefused,
)

from koma_bell.exceptions import NotifyError
from koma_bell.secrets import get_mail_credentials

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_STARTTLS_PORT = 587
SMTP_TIMEOUT = 10


class SMTPMailer:
    def __init__(self, user: str, auth_code: str, to: str) -> None:
        self.user = user
        self.auth_code = auth_code
        self.to = to

    @classmethod
    def from_env(cls) -> "SMTPMailer":
        try:
            credentials = get_mail_credentials()
        except Exception as exc:
            raise NotifyError(str(exc)) from exc
        return cls(
            user=credentials.user,
            auth_code=credentials.auth_code,
            to=credentials.to,
        )

    def send(
        self,
        subject: str,
        body: str,
        progress: Callable[[str], None] | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = self.user
        message["To"] = self.to
        message["Subject"] = subject
        message.set_content(body)
        errors: list[str] = []
        for sender in (self._send_ssl, self._send_starttls):
            try:
                sender(message, progress)
                return
            except NotifyError as exc:
                errors.append(str(exc))
                _progress(progress, f"失败：{exc}")
        raise NotifyError("Mail send failed. " + " | ".join(errors))

    def _send_ssl(
        self,
        message: EmailMessage,
        progress: Callable[[str], None] | None,
    ) -> None:
        try:
            _progress(progress, f"连接 {SMTP_HOST}:{SMTP_PORT} SSL...")
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
                _progress(progress, "SSL 已连接，发送 EHLO...")
                smtp.ehlo()
                _progress(progress, "正在登录 SMTP...")
                smtp.login(self.user, self.auth_code)
                _progress(progress, "登录成功，正在发送邮件...")
                smtp.send_message(message, from_addr=self.user, to_addrs=[self.to])
        except Exception as exc:
            _raise_notify_error(exc)

    def _send_starttls(
        self,
        message: EmailMessage,
        progress: Callable[[str], None] | None,
    ) -> None:
        try:
            _progress(progress, f"连接 {SMTP_HOST}:{SMTP_STARTTLS_PORT} STARTTLS...")
            with smtplib.SMTP(SMTP_HOST, SMTP_STARTTLS_PORT, timeout=SMTP_TIMEOUT) as smtp:
                _progress(progress, "已连接，发送 EHLO...")
                smtp.ehlo()
                _progress(progress, "启动 TLS...")
                smtp.starttls()
                smtp.ehlo()
                _progress(progress, "正在登录 SMTP...")
                smtp.login(self.user, self.auth_code)
                _progress(progress, "登录成功，正在发送邮件...")
                smtp.send_message(message, from_addr=self.user, to_addrs=[self.to])
        except Exception as exc:
            _raise_notify_error(exc)


def _raise_notify_error(exc: BaseException) -> None:
    if isinstance(exc, SMTPAuthenticationError):
        raise NotifyError(
            "SMTP authentication failed. 请确认已开启邮箱 SMTP 服务，"
            "并使用 SMTP 授权码而不是邮箱登录密码。"
        ) from exc
    if isinstance(exc, SMTPSenderRefused):
        raise NotifyError(f"SMTP rejected sender: {_smtp_error(exc)}") from exc
    if isinstance(exc, SMTPRecipientsRefused):
        raise NotifyError(f"SMTP rejected recipient: {exc.recipients}") from exc
    if isinstance(exc, SMTPConnectError):
        raise NotifyError(f"Cannot connect to SMTP server: {_smtp_error(exc)}") from exc
    if isinstance(exc, SMTPResponseException):
        raise NotifyError(f"SMTP error: {_smtp_error(exc)}") from exc
    if isinstance(exc, (OSError, SMTPException)):
        raise NotifyError(f"{type(exc).__name__}: {exc}") from exc
    raise NotifyError(f"{type(exc).__name__}: {exc}") from exc


def _progress(progress: Callable[[str], None] | None, message: str) -> None:
    if progress is not None:
        progress(message)


def _smtp_error(exc: SMTPResponseException) -> str:
    message = exc.smtp_error
    if isinstance(message, bytes):
        message = message.decode("utf-8", errors="replace")
    return f"{exc.smtp_code} {message}"
