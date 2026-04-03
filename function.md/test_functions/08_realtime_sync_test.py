import socket

from test_helpers import CaseCollector, print_summary


def websocket_handshake(host="127.0.0.1", port=8000):
    request_text = (
        "GET /ws/realtime/ HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(request_text.encode("utf-8"))
        return sock.recv(1024).decode("utf-8", errors="replace")


def main():
    collector = CaseCollector("08 Realtime Sync Tests")
    try:
        response = websocket_handshake()
        collector.check(
            "websocket_endpoint_responds",
            "101 Switching Protocols" in response or "403" in response or "401" in response,
            response.splitlines()[0] if response else "no response",
        )
    except Exception as exc:
        collector.check("websocket_endpoint_responds", False, str(exc))
    return print_summary("08 Realtime Sync Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
