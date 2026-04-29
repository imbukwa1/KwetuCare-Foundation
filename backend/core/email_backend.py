import smtplib
import socket

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")

        last_error = None
        for family, socktype, proto, _, address in socket.getaddrinfo(
            host,
            port,
            socket.AF_INET,
            socket.SOCK_STREAM,
        ):
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                if timeout is not None:
                    sock.settimeout(timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(address)
                return sock
            except OSError as exc:
                last_error = exc
                if sock is not None:
                    sock.close()

        if last_error is not None:
            raise last_error
        raise OSError(f"No IPv4 SMTP address found for {host}:{port}")


class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        raw_socket = IPv4SMTP._get_socket(self, host, port, timeout)
        return self.context.wrap_socket(raw_socket, server_hostname=self._host)


class IPv4GmailSMTPEmailBackend(SMTPEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_class = IPv4SMTP_SSL if self.use_ssl else IPv4SMTP
