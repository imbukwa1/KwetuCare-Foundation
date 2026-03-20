from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def ping(request):
    return JsonResponse({'status': 'ok', 'message': 'Kwetu Care backend is working'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('ping/', ping),
    path('api/', include('core.urls')),
]
