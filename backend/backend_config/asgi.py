import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_config.settings')

django_asgi_app = get_asgi_application()

from core.realtime import updates_socket


async def application(scope, receive, send):
    if scope['type'] == 'websocket' and scope.get('path') == '/ws/updates/':
        await updates_socket(scope, receive, send)
        return

    await django_asgi_app(scope, receive, send)
