import asyncio
import json
import threading
from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

_CLIENTS = set()
_LOOP = None
_LOCK = threading.Lock()

EVENT_MAP = {
    "patient_registered": ["patient_created"],
    "triage_completed": ["triage_completed"],
    "consultation_completed": ["consultation_completed", "prescription_updated"],
    "pharmacy_dispensed": ["prescription_updated", "drug_dispensed"],
    "inventory_created": ["inventory_created"],
    "inventory_restocked": ["inventory_restocked"],
    "user_approved": ["user_approved"],
    "user_rejected": ["user_rejected"],
}


def _build_message(event_type, payload=None):
    return json.dumps({"type": event_type, **(payload or {})})


def publish_event(event_type, payload=None):
    with _LOCK:
        loop = _LOOP
        clients = list(_CLIENTS)

    if not loop or not clients:
        return

    message = _build_message(event_type, payload)

    def _dispatch():
        stale_clients = []
        for queue in clients:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(message)
                except Exception:
                    stale_clients.append(queue)
            except Exception:
                stale_clients.append(queue)

        if stale_clients:
            with _LOCK:
                for queue in stale_clients:
                    _CLIENTS.discard(queue)

    loop.call_soon_threadsafe(_dispatch)


def publish_audit_event(*, action, patient=None, details=None):
    payload = {
        "action": action,
        "patient_id": getattr(patient, "id", None),
        "reg_no": getattr(patient, "reg_no", None),
        "status": getattr(patient, "status", None),
        "details": details or {},
    }
    for event_type in EVENT_MAP.get(action, []):
        publish_event(event_type, payload)


def _get_user_from_token(token):
    if not token:
        return None

    try:
        access_token = AccessToken(token)
        user_id = access_token.get("user_id")
        if not user_id:
            return None
        user_model = get_user_model()
        return user_model.objects.filter(id=user_id).only("id").first()
    except Exception:
        return None


async def _authenticate(scope):
    query_params = parse_qs(scope.get("query_string", b"").decode())
    token = query_params.get("token", [None])[0]
    return await asyncio.to_thread(_get_user_from_token, token)


def _register_client(queue):
    global _LOOP
    with _LOCK:
        _LOOP = asyncio.get_running_loop()
        _CLIENTS.add(queue)


def _unregister_client(queue):
    with _LOCK:
        _CLIENTS.discard(queue)


async def updates_socket(scope, receive, send):
    user = await _authenticate(scope)
    if user is None:
        await send({"type": "websocket.close", "code": 4401})
        return

    queue = asyncio.Queue(maxsize=100)
    _register_client(queue)

    await send({"type": "websocket.accept"})
    await send({"type": "websocket.send", "text": _build_message("connected", {"user_id": user.id})})

    async def _sender():
        while True:
            message = await queue.get()
            await send({"type": "websocket.send", "text": message})

    sender_task = asyncio.create_task(_sender())

    try:
        while True:
            event = await receive()
            if event["type"] == "websocket.disconnect":
                break
            if event["type"] == "websocket.receive" and event.get("text") == "ping":
                await send({"type": "websocket.send", "text": _build_message("pong")})
    finally:
        _unregister_client(queue)
        sender_task.cancel()
        await asyncio.gather(sender_task, return_exceptions=True)
