from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path


def ping(request):
    return JsonResponse({'status': 'ok', 'message': 'Kwetu Care backend is working'})


def websocket_probe(request):
    return HttpResponse("WebSocket authentication required.", status=403)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('ping/', ping),
    path('ws/realtime/', websocket_probe),
    path('ws/updates/', websocket_probe),
    path('api/', include('core.urls')),
]
