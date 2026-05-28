from smtplib import SMTPAuthenticationError, SMTPServerDisconnected
from unittest.mock import Mock, patch

import pytest

from koma_bell.exceptions import NotifyError
from koma_bell.mail.smtp import SMTPMailer


def test_smtp_mailer_uses_smtp_ssl():
    smtp = Mock()
    smtp.__enter__ = Mock(return_value=smtp)
    smtp.__exit__ = Mock(return_value=False)

    with patch("koma_bell.mail.smtp.smtplib.SMTP_SSL", return_value=smtp) as smtp_ssl:
        SMTPMailer("from@qq.com", "auth-code", "to@qq.com").send("subject", "body")

    smtp_ssl.assert_called_once_with("smtp.qq.com", 465, timeout=10)
    smtp.ehlo.assert_called_once()
    smtp.login.assert_called_once_with("from@qq.com", "auth-code")
    smtp.send_message.assert_called_once()


def test_smtp_mailer_retries_transient_failures():
    smtp = Mock()
    smtp.__enter__ = Mock(return_value=smtp)
    smtp.__exit__ = Mock(return_value=False)

    with (
        patch(
            "koma_bell.mail.smtp.smtplib.SMTP_SSL",
            side_effect=[SMTPServerDisconnected("closed"), smtp],
        ) as smtp_ssl,
        patch(
            "koma_bell.mail.smtp.smtplib.SMTP",
            side_effect=SMTPServerDisconnected("closed"),
        ) as smtp_starttls,
        patch("koma_bell.mail.smtp.time.sleep") as sleep,
    ):
        SMTPMailer("from@qq.com", "auth-code", "to@qq.com").send("subject", "body")

    assert smtp_ssl.call_count == 2
    assert smtp_starttls.call_count == 1
    sleep.assert_called_once_with(30)
    smtp.send_message.assert_called_once()


def test_smtp_mailer_does_not_retry_authentication_errors():
    with (
        patch(
            "koma_bell.mail.smtp.smtplib.SMTP_SSL",
            side_effect=SMTPAuthenticationError(535, b"auth failed"),
        ) as smtp_ssl,
        patch("koma_bell.mail.smtp.smtplib.SMTP") as smtp_starttls,
        patch("koma_bell.mail.smtp.time.sleep") as sleep,
        pytest.raises(NotifyError, match="authentication failed"),
    ):
        SMTPMailer("from@qq.com", "bad-auth-code", "to@qq.com").send("subject", "body")

    smtp_ssl.assert_called_once()
    smtp_starttls.assert_not_called()
    sleep.assert_not_called()
