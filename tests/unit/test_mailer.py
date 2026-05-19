from unittest.mock import Mock, patch

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
