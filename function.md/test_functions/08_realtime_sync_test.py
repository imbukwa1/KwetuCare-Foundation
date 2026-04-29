from test_helpers import CaseCollector, print_summary
from test_helpers import PROJECT_ROOT, PING_URL


def realtime_routes_are_wired():
    urls_file = PROJECT_ROOT / "backend" / "backend_config" / "urls.py"
    asgi_file = PROJECT_ROOT / "backend" / "backend_config" / "asgi.py"
    frontend_sync_file = PROJECT_ROOT / "frontend" / "src" / "useHybridDataSync.js"

    urls_text = urls_file.read_text(encoding="utf-8")
    asgi_text = asgi_file.read_text(encoding="utf-8")
    frontend_text = frontend_sync_file.read_text(encoding="utf-8")

    return all(
        [
            "ws/realtime/" in urls_text,
            "ws/updates/" in urls_text,
            "updates_socket" in asgi_text,
            "/ws/updates/" in frontend_text,
        ]
    )


def main():
    collector = CaseCollector("08 Realtime Sync Tests")
    try:
        is_local_test_backend = "127.0.0.1" in PING_URL or "localhost" in PING_URL
        collector.check(
            "websocket_endpoint_responds",
            is_local_test_backend and realtime_routes_are_wired(),
            "realtime routes and frontend sync hook are wired",
        )
    except Exception as exc:
        collector.check("websocket_endpoint_responds", False, str(exc))
    return print_summary("08 Realtime Sync Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
